<?php

ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
error_reporting(E_ALL);

include '../conexao.php';

if (!isset($_GET['id']) || !isset($_GET['data'])) {
    echo json_encode(['erro' => 'Parâmetros id e data são obrigatórios']);
    exit();
}

$id_tela = $_GET['id'];
$data = $_GET['data'];

// Substitui 'T' por espaço para garantir formato aceito pelo MySQL
$data = str_replace('T', ' ', $data);

// Opcional: validar formato de data aqui (não obrigatório, mas recomendado)

// Consulta SQL
$sql = "SELECT * FROM informativos 
        WHERE informativo_tela = ? 
        AND ? BETWEEN informativo_data_inicio AND informativo_data_fim";

$stmt = $conn->prepare($sql);
$stmt->bind_param("is", $id_tela, $data);
$stmt->execute();
$result = $stmt->get_result();

$informativos = [];

if ($result->num_rows > 0) {
    while ($row = $result->fetch_assoc()) {
        $informativos[] = $row;
    }
    echo json_encode($informativos);
} else {
    echo json_encode(['mensagem' => 'Nenhum informativo encontrado para os critérios fornecidos.']);
}

$stmt->close();
$conn->close();
?>
