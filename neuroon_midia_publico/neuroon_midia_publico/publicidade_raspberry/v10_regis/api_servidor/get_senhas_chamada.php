<?php

ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
error_reporting(E_ALL);

header('Content-Type: application/json; charset=utf-8');

include __DIR__ . '/../conexao.php';

$conn->set_charset("utf8mb4");

$id_local_param = $_GET['id_local'] ?? $_GET['id_tela'] ?? $_GET['id'] ?? null;

if ($id_local_param === null || $id_local_param === '') {
    echo json_encode(['erro' => 'Parametro obrigatorio nao fornecido: id_local']);
    exit();
}

$id_local = (int) $id_local_param;

if ($id_local <= 0) {
    echo json_encode(['erro' => 'Parametro id_local invalido']);
    exit();
}

$stmt_aparelho = $conn->prepare("SELECT cliente FROM locais WHERE id_local = ? LIMIT 1");

if (!$stmt_aparelho) {
    echo json_encode(['erro' => 'Erro na preparacao da consulta de aparelho: ' . $conn->error]);
    exit();
}

$stmt_aparelho->bind_param("i", $id_local);
$stmt_aparelho->execute();
$result_aparelho = $stmt_aparelho->get_result();

if ($result_aparelho->num_rows === 0) {
    echo json_encode([]);
    $stmt_aparelho->close();
    $conn->close();
    exit();
}

$aparelho = $result_aparelho->fetch_assoc();
$cliente = $aparelho['cliente'];
$stmt_aparelho->close();

if ($cliente === null || $cliente === '') {
    echo json_encode([]);
    $conn->close();
    exit();
}

$order_column = 'senha';
$candidate_columns = ['id', 'id_senha', 'criado_em', 'created_at', 'data_criacao'];

foreach ($candidate_columns as $candidate_column) {
    $stmt_column = $conn->prepare(
        "SELECT COLUMN_NAME
         FROM INFORMATION_SCHEMA.COLUMNS
         WHERE TABLE_SCHEMA = DATABASE()
         AND TABLE_NAME = 'senhas'
         AND COLUMN_NAME = ?
         LIMIT 1"
    );

    if (!$stmt_column) {
        echo json_encode(['erro' => 'Erro ao verificar colunas de senhas: ' . $conn->error]);
        $conn->close();
        exit();
    }

    $stmt_column->bind_param("s", $candidate_column);
    $stmt_column->execute();
    $result_column = $stmt_column->get_result();

    if ($result_column->num_rows > 0) {
        $order_column = $candidate_column;
        $stmt_column->close();
        break;
    }

    $stmt_column->close();
}

$sql_senhas = "SELECT senha, cliente_nome, qtd_pessoas
        FROM senhas
        WHERE cliente_id = ?
        AND status = 2
        ORDER BY {$order_column} DESC";

$stmt_senhas = $conn->prepare($sql_senhas);

if (!$stmt_senhas) {
    echo json_encode(['erro' => 'Erro na preparacao da consulta de senhas: ' . $conn->error]);
    $conn->close();
    exit();
}

if (is_numeric($cliente)) {
    $cliente_id = (int) $cliente;
    $stmt_senhas->bind_param("i", $cliente_id);
} else {
    $cliente_id = (string) $cliente;
    $stmt_senhas->bind_param("s", $cliente_id);
}

$stmt_senhas->execute();
$result_senhas = $stmt_senhas->get_result();

$senhas = [];
while ($row = $result_senhas->fetch_assoc()) {
    $senhas[] = [
        'senha' => $row['senha'],
        'cliente_nome' => $row['cliente_nome'],
        'qtd_pessoas' => $row['qtd_pessoas']
    ];
}

echo json_encode($senhas);

$stmt_senhas->close();
$conn->close();
?>
