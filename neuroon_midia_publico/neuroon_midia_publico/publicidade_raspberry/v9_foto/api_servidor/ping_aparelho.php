<?php

ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
error_reporting(E_ALL);

header('Content-Type: application/json; charset=utf-8');

include __DIR__ . '/../conexao.php';

$conn->set_charset("utf8mb4");

$id_aparelho_param = $_GET['id_tela'] ?? $_GET['id_aparelho'] ?? $_GET['id'] ?? null;

if ($id_aparelho_param === null || $id_aparelho_param === '') {
    echo json_encode(['erro' => 'Parametro obrigatorio nao fornecido: id_tela']);
    exit();
}

$id_aparelho = (int) $id_aparelho_param;

if ($id_aparelho <= 0) {
    echo json_encode(['erro' => 'Parametro id_tela invalido']);
    exit();
}

$ip = null;
if (!empty($_SERVER['HTTP_X_FORWARDED_FOR'])) {
    $forwarded_ips = explode(',', $_SERVER['HTTP_X_FORWARDED_FOR']);
    $ip = trim($forwarded_ips[0]);
} elseif (!empty($_SERVER['REMOTE_ADDR'])) {
    $ip = trim($_SERVER['REMOTE_ADDR']);
}

if ($ip !== null) {
    $ip = substr($ip, 0, 45);
}

$versao_app = $_GET['versao_app'] ?? null;
if ($versao_app !== null) {
    $versao_app = trim($versao_app);
    $versao_app = $versao_app === '' ? null : substr($versao_app, 0, 50);
}

$sql = "INSERT INTO aparelhos_status (id_aparelho, ultimo_ping, status, ip, versao_app)
        VALUES (?, NOW(), 'online', ?, ?)
        ON DUPLICATE KEY UPDATE
            ultimo_ping = NOW(),
            status = 'online',
            ip = VALUES(ip),
            versao_app = VALUES(versao_app),
            atualizado_em = CURRENT_TIMESTAMP";

$stmt = $conn->prepare($sql);

if (!$stmt) {
    echo json_encode(['erro' => 'Erro na preparacao da query: ' . $conn->error]);
    exit();
}

$stmt->bind_param("iss", $id_aparelho, $ip, $versao_app);

if ($stmt->execute()) {
    echo json_encode([
        'success' => true,
        'mensagem' => 'Ping registrado com sucesso',
        'id_aparelho' => $id_aparelho
    ]);
} else {
    echo json_encode(['erro' => 'Erro na execucao da query: ' . $stmt->error]);
}

$stmt->close();
$conn->close();
?>
