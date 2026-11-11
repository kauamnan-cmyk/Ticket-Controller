<?php

ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
error_reporting(E_ALL);

include '../conexao.php';

// Força charset UTF-8 na conexão
$conn->set_charset("utf8mb4");

// Verifica se todos os parâmetros foram passados
if (!isset($_GET['exibicao_qtd'], $_GET['id_tela'], $_GET['id_conteudo'])) {
    echo json_encode(['erro' => 'Parâmetros obrigatórios não fornecidos: exibicao_qtd, id_tela, id_conteudo']);
    exit();
}

$exibicao_qtd = (int) $_GET['exibicao_qtd'];
$id_tela = (int) $_GET['id_tela'];
$id_conteudo = (int) $_GET['id_conteudo'];

// Prepara a query para atualizar somando exibicao_qtd
$sql = "UPDATE publicidades SET exibicoes = exibicoes + ? WHERE id_aparelho = ? AND id_conteudo = ?";
$stmt = $conn->prepare($sql);

if (!$stmt) {
    echo json_encode(['erro' => 'Erro na preparação da query: ' . $conn->error]);
    exit();
}

$stmt->bind_param("iii", $exibicao_qtd, $id_tela, $id_conteudo);

if ($stmt->execute()) {
    if ($stmt->affected_rows > 0) {
        echo json_encode(['success' => 'Exibição atualizada com sucesso']);
    } else {
        echo json_encode(['info' => 'Nenhum registro atualizado. Verifique se id_tela e id_conteudo existem']);
    }
} else {
    echo json_encode(['erro' => 'Erro na execução da query: ' . $stmt->error]);
}

$stmt->close();
$conn->close();
