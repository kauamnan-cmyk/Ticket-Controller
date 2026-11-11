<?php
declare(strict_types=1);

header('Content-Type: application/json; charset=utf-8');
header('X-Content-Type-Options: nosniff');
header('Cache-Control: no-store, no-cache, must-revalidate, max-age=0');
header('Referrer-Policy: no-referrer');

$allowedOrigins = [
    'https://example.com',
    'https://example.com',
];
$origin = $_SERVER['HTTP_ORIGIN'] ?? '';
$isLocalDevelopmentOrigin = preg_match('/^http:\/\/(localhost|127\.0\.0\.1):[0-9]+$/', $origin) === 1;

if (in_array($origin, $allowedOrigins, true) || $isLocalDevelopmentOrigin) {
    header('Access-Control-Allow-Origin: ' . $origin);
    header('Access-Control-Allow-Credentials: true');
    header('Access-Control-Allow-Headers: Content-Type, Accept');
    header('Access-Control-Allow-Methods: GET, OPTIONS');
    header('Vary: Origin');
}

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(204);
    exit;
}

function jsonResponse(int $statusCode, array $payload): void
{
    http_response_code($statusCode);
    echo json_encode($payload);
    exit;
}

function fetchPreparedRows(mysqli_stmt $stmt): array
{
    $metadata = $stmt->result_metadata();

    if (!$metadata) {
        return [];
    }

    $row = [];
    $fields = [];
    $bind = [];

    while ($field = $metadata->fetch_field()) {
        $fields[] = $field->name;
        $row[$field->name] = null;
        $bind[] = &$row[$field->name];
    }

    $stmt->bind_result(...$bind);
    $rows = [];

    while ($stmt->fetch()) {
        $item = [];

        foreach ($fields as $field) {
            $item[$field] = $row[$field];
        }

        $rows[] = $item;
    }

    return $rows;
}

function startApiSession(): void
{
    if (session_status() === PHP_SESSION_ACTIVE) {
        return;
    }

    $isHttps = (
        (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off')
        || (($_SERVER['HTTP_X_FORWARDED_PROTO'] ?? '') === 'https')
    );
    $origin = $_SERVER['HTTP_ORIGIN'] ?? '';
    $allowedOrigins = ['https://example.com', 'https://example.com'];
    $useCrossSiteCookie = $origin !== '' && !in_array($origin, $allowedOrigins, true);

    session_set_cookie_params([
        'lifetime' => 0,
        'path' => '/',
        'domain' => '',
        'secure' => $isHttps,
        'httponly' => true,
        'samesite' => $useCrossSiteCookie ? 'None' : 'Lax',
    ]);

    session_start();
}

function formatSenha(array $row): array
{
    return [
        'id' => (int) $row['id'],
        'cliente_id' => (int) $row['cliente_id'],
        'senha' => (string) $row['senha'],
        'cliente_nome' => (string) $row['cliente_nome'],
        'status' => (string) $row['status'],
        'gerada' => (string) $row['gerada'],
        'telefone' => (string) $row['telefone'],
        'qtd_pessoas' => (int) $row['qtd_pessoas'],
        'qtd_cadeirantes' => isset($row['qtd_cadeirantes']) ? (int) $row['qtd_cadeirantes'] : 0,
        'qtd_criancas' => isset($row['qtd_criancas']) ? (int) $row['qtd_criancas'] : 0,
        'chamado_em' => isset($row['chamado_em']) ? (string) $row['chamado_em'] : null,
        'cancelado_em' => isset($row['cancelado_em']) ? (string) $row['cancelado_em'] : null,
        'confirmado_em' => isset($row['confirmado_em']) ? (string) $row['confirmado_em'] : null,
        'chamadas_total' => isset($row['chamadas_total']) ? (int) $row['chamadas_total'] : 0,
    ];
}

if ($_SERVER['REQUEST_METHOD'] !== 'GET') {
    header('Allow: GET, OPTIONS');
    jsonResponse(405, ['success' => false, 'message' => 'Método não permitido.']);
}

startApiSession();

$usuarioId = (int) ($_SESSION['usuario_id'] ?? 0);
$tipoUsuario = (string) ($_SESSION['usuario_tipo'] ?? 'admin');
$clienteId = (int) ($_SESSION['cliente_id'] ?? 0);

if (empty($_SESSION['autenticado']) || $usuarioId <= 0) {
    jsonResponse(401, ['success' => false, 'message' => 'Sessão inválida. Faça login novamente.']);
}

$configFile = __DIR__ . '/../../config.php';

if (!is_file($configFile)) {
    error_log('Config controle_acesso não encontrado em: ' . $configFile);
    jsonResponse(500, ['success' => false, 'message' => 'Arquivo de configuração da API não encontrado.']);
}

require $configFile;

if (!isset($conn) || !($conn instanceof mysqli)) {
    jsonResponse(500, ['success' => false, 'message' => 'Conexão com banco não inicializada.']);
}

try {
    $statusValidos = ['1', '2', '3', '4', '5'];
    $statusPermitidos = $statusValidos;
    $statusPrincipal = 'ativos';

    if ($tipoUsuario === 'cliente') {
        $usuarioStmt = $conn->prepare('SELECT controle_status_permitidos, controle_status_principal FROM usuarios WHERE id = ? LIMIT 1');
        $usuarioStmt->bind_param('i', $usuarioId);
        $usuarioStmt->execute();
        $usuarioRows = fetchPreparedRows($usuarioStmt);
        $usuarioConfig = $usuarioRows[0] ?? [];

        $statusPermitidos = array_values(array_intersect(
            $statusValidos,
            array_filter(array_map('trim', explode(',', (string) ($usuarioConfig['controle_status_permitidos'] ?? '1,2'))))
        ));

        if (count($statusPermitidos) === 0) {
            $statusPermitidos = ['1', '2'];
        }

        $statusPrincipal = (string) ($usuarioConfig['controle_status_principal'] ?? 'ativos');

        if ($statusPrincipal === 'ativos' && (!in_array('1', $statusPermitidos, true) || !in_array('2', $statusPermitidos, true))) {
            $statusPrincipal = $statusPermitidos[0];
        } elseif ($statusPrincipal !== 'ativos' && !in_array($statusPrincipal, $statusPermitidos, true)) {
            $statusPrincipal = $statusPermitidos[0];
        }
    }

    $todayStart = date('Y-m-d 00:00:00');
    $todayEnd = date('Y-m-d 23:59:59');
    if ($clienteId > 0) {
        $stmt = $conn->prepare(
            'SELECT s.id, s.cliente_id, s.senha, s.cliente_nome, s.status, s.gerada, s.telefone, s.qtd_pessoas, s.qtd_cadeirantes, s.qtd_criancas,
                    (SELECT sh.data_hora FROM senhas_historico sh WHERE sh.senha_id = s.id AND sh.status_novo = 2 ORDER BY sh.id DESC LIMIT 1) AS chamado_em,
                    (SELECT sh.data_hora FROM senhas_historico sh WHERE sh.senha_id = s.id AND sh.status_novo = 5 ORDER BY sh.id DESC LIMIT 1) AS cancelado_em,
                    (SELECT sh.data_hora FROM senhas_historico sh WHERE sh.senha_id = s.id AND sh.status_novo = 4 ORDER BY sh.id DESC LIMIT 1) AS confirmado_em,
                    (SELECT COUNT(*) FROM senhas_historico sh WHERE sh.senha_id = s.id AND sh.status_novo = 2) AS chamadas_total
             FROM senhas s
             WHERE s.cliente_id = ?
               AND s.gerada >= ?
               AND s.gerada <= ?
             ORDER BY s.gerada ASC, s.id ASC'
        );
        $stmt->bind_param('iss', $clienteId, $todayStart, $todayEnd);
    } else {
        $stmt = $conn->prepare(
            'SELECT s.id, s.cliente_id, s.senha, s.cliente_nome, s.status, s.gerada, s.telefone, s.qtd_pessoas,
                    (SELECT sh.data_hora FROM senhas_historico sh WHERE sh.senha_id = s.id AND sh.status_novo = 2 ORDER BY sh.id DESC LIMIT 1) AS chamado_em,
                    (SELECT sh.data_hora FROM senhas_historico sh WHERE sh.senha_id = s.id AND sh.status_novo = 5 ORDER BY sh.id DESC LIMIT 1) AS cancelado_em,
                    (SELECT sh.data_hora FROM senhas_historico sh WHERE sh.senha_id = s.id AND sh.status_novo = 4 ORDER BY sh.id DESC LIMIT 1) AS confirmado_em,
                    (SELECT COUNT(*) FROM senhas_historico sh WHERE sh.senha_id = s.id AND sh.status_novo = 2) AS chamadas_total
             FROM senhas s
             WHERE s.gerada >= ?
               AND s.gerada <= ?
             ORDER BY s.gerada ASC, s.id ASC'
        );
        $stmt->bind_param('ss', $todayStart, $todayEnd);
    }

    $stmt->execute();
    $senhas = [];

    foreach (fetchPreparedRows($stmt) as $row) {
        if ($tipoUsuario === 'cliente' && !in_array((string) $row['status'], $statusPermitidos, true)) {
            continue;
        }

        $senhas[] = formatSenha($row);
    }

    jsonResponse(200, [
        'success' => true,
        'usuario' => [
            'id' => $usuarioId,
            'nome' => (string) ($_SESSION['usuario_nome'] ?? 'Usuário'),
            'tipo_usuario' => $tipoUsuario === 'cliente' ? 'cliente' : 'admin',
            'cliente_id' => $clienteId ?: null,
            'controle_status_permitidos' => $statusPermitidos,
            'controle_status_principal' => $statusPrincipal,
        ],
        'senhas' => $senhas,
    ]);
} catch (mysqli_sql_exception $exception) {
    error_log('Erro controle_acesso/senhas: ' . $exception->getMessage());

    jsonResponse(500, ['success' => false, 'message' => 'Erro interno ao carregar senhas.']);
}
