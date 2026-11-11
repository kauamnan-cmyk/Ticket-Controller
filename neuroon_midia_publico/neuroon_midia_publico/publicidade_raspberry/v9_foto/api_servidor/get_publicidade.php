<?php

ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
error_reporting(E_ALL);

include '../conexao.php';

if (!isset($_GET['id'])) {
    echo json_encode(['erro' => 'ID do aparelho não fornecido']);
    exit();
}

$id_aparelho = $_GET['id'];

// Consultar o banco de dados para buscar as mídias associadas ao ID do aparelho
$sql = "SELECT id_conteudo, url_midia
        FROM publicidades
        WHERE id_aparelho = ?
        AND status = 0
        AND NOW() BETWEEN inicio AND fim";
$stmt = $conn->prepare($sql);
$stmt->bind_param("i", $id_aparelho);
$stmt->execute();
$result = $stmt->get_result();

// Verificar se há mídias associadas ao ID do aparelho
if ($result->num_rows > 0) {
    $midias = [];
    while ($row = $result->fetch_assoc()) {
        $midias[] = [
            'id_conteudo' => $row['id_conteudo'],
            'url_midia' => "https://example.com/nextpub/" . $row['url_midia']
        ];
    }

    // Retornar as mídias com id_conteudo e url_midia em formato JSON
    echo json_encode($midias);
} else {
    echo json_encode(['erro' => 'Nenhuma mídia encontrada para este aparelho']);
}

$stmt->close();
$conn->close();
?>
