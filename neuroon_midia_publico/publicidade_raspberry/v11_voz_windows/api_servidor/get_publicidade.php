<?php

ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
error_reporting(E_ALL);

include '../conexao.php';

$id_local_param = $_GET['id_local'] ?? $_GET['id_tela'] ?? $_GET['id'] ?? null;

if ($id_local_param === null || $id_local_param === '') {
    echo json_encode(['erro' => 'ID do local nao fornecido']);
    exit();
}

$id_local = (int) $id_local_param;

// Consultar o banco de dados para buscar as midias associadas ao ID do local
$sql = "SELECT id_conteudo, url_midia
        FROM publicidades
        WHERE id_local = ?
        AND status = 0
        AND NOW() BETWEEN inicio AND fim";
$stmt = $conn->prepare($sql);
$stmt->bind_param("i", $id_local);
$stmt->execute();
$result = $stmt->get_result();

// Verificar se há mídias associadas ao ID do aparelho
if ($result->num_rows > 0) {
    $midias = [];
    while ($row = $result->fetch_assoc()) {
        $midias[] = [
            'id_conteudo' => $row['id_conteudo'],
            'url_midia' => "https://example.com/nextpubli/" . $row['url_midia']
        ];
    }

    // Retornar as mídias com id_conteudo e url_midia em formato JSON
    echo json_encode($midias);
} else {
    echo json_encode(['erro' => 'Nenhuma midia encontrada para este local']);
}

$stmt->close();
$conn->close();
?>
