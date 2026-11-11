<?php

ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
error_reporting(E_ALL);

// Forçar cabeçalho UTF-8
header('Content-Type: application/json; charset=utf-8');

include '../conexao.php';

// Forçar charset UTF-8 na conexão MySQL
$conn->set_charset('utf8mb4');

// Verificar se os parâmetros foram fornecidos
if (!isset($_GET['exibicao_conteudo']) || !isset($_GET['exibicao_tela'])) {
    echo json_encode(['erro' => 'Parâmetros exibicao_conteudo e exibicao_tela são obrigatórios'], JSON_UNESCAPED_UNICODE);
    exit();
}

$conteudo = (int)$_GET['exibicao_conteudo'];
$tela = (int)$_GET['exibicao_tela'];

// Definir os 4 horários do dia
$data_base = date('Y-m-d');
$horarios = ['00:00:00', '06:00:00', '12:00:00', '18:00:00'];

$sql = "INSERT INTO exibicoes (exibicao_conteudo, exibicao_tela, exibicao_data) VALUES (?, ?, ?)";
$stmt = $conn->prepare($sql);

if (!$stmt) {
    echo json_encode(['erro' => 'Erro ao preparar statement: ' . $conn->error], JSON_UNESCAPED_UNICODE);
    exit();
}

$sucesso = true;

foreach ($horarios as $hora) {
    $data_completa = $data_base . ' ' . $hora;
    $stmt->bind_param("iis", $conteudo, $tela, $data_completa);
    if (!$stmt->execute()) {
        $sucesso = false;
        break;
    }
}

$stmt->close();
$conn->close();

if ($sucesso) {
    echo json_encode(['sucesso' => '4 registros inseridos com sucesso'], JSON_UNESCAPED_UNICODE);
} else {
    echo json_encode(['erro' => 'Falha ao inserir um ou mais registros'], JSON_UNESCAPED_UNICODE);
}
?>
