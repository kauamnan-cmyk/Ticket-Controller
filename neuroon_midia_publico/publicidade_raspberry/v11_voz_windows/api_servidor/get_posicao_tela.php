<?php

ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
error_reporting(E_ALL);

include '../conexao.php';

$id_local_param = $_GET['id_local'] ?? $_GET['id_tela'] ?? $_GET['id'] ?? null;

if ($id_local_param === null || $id_local_param === '') {
    echo json_encode(['erro' => 'Parâmetro id_tela é obrigatório']);
    exit();
}

$id_local = (int) $id_local_param;

// Consulta SQL para buscar o formato_tela da tela especificada
$sql = "SELECT formato_tela FROM locais WHERE id_local = ?";
$stmt = $conn->prepare($sql);
$stmt->bind_param("i", $id_local);
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
