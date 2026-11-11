<?php

ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
error_reporting(E_ALL);

include '../conexao.php';

if (!isset($_GET['id_tela'])) {
    echo json_encode(['erro' => 'Parâmetro id_tela é obrigatório']);
    exit();
}

$id_tela = $_GET['id_tela'];

// Consulta SQL para buscar o formato_tela da tela especificada
$sql = "SELECT formato_tela FROM telas WHERE aparelho_tela = ?";
$stmt = $conn->prepare($sql);
$stmt->bind_param("i", $id_tela);
$stmt->execute();
$result = $stmt->get_result();

if ($result->num_rows > 0) {
    $linha = $result->fetch_assoc();
    echo json_encode(['formato_tela' => $linha['formato_tela']]);
} else {
    echo json_encode(['mensagem' => 'Tela não encontrada']);
}

$stmt->close();
$conn->close();
?>
