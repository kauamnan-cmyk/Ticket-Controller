<?php

ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
error_reporting(E_ALL);

header('Content-Type: application/json; charset=utf-8');

include __DIR__ . '/../conexao.php';

$conn->set_charset("utf8mb4");

function json_response($payload) {
    echo json_encode($payload, JSON_UNESCAPED_UNICODE);
    exit();
}

$id_local_param = $_GET['id_local'] ?? $_GET['id_tela'] ?? $_GET['id'] ?? null;
$id_conteudo_param = $_GET['id_conteudo'] ?? $_GET['id_publicidade'] ?? null;
$exibido_em_param = $_GET['exibido_em'] ?? null;

if ($id_local_param === null || $id_local_param === '' || $id_conteudo_param === null || $id_conteudo_param === '' || $exibido_em_param === null || $exibido_em_param === '') {
    json_response(['erro' => 'Parâmetros obrigatórios não fornecidos: id_local, id_conteudo, exibido_em']);
}

$id_local = (int) $id_local_param;
$id_conteudo = (int) $id_conteudo_param;

if ($id_local <= 0) {
    json_response(['erro' => 'Parâmetro id_local inválido']);
}

if ($id_conteudo <= 0) {
    json_response(['erro' => 'Parâmetro id_conteudo inválido']);
}

$exibido_em = DateTime::createFromFormat('Y-m-d H:i:s', $exibido_em_param);
$exibido_em_errors = DateTime::getLastErrors();

if (
    !$exibido_em
    || ($exibido_em_errors !== false && ($exibido_em_errors['warning_count'] > 0 || $exibido_em_errors['error_count'] > 0))
    || $exibido_em->format('Y-m-d H:i:s') !== $exibido_em_param
) {
    json_response(['erro' => 'Parâmetro exibido_em inválido. Use o formato YYYY-MM-DD HH:MM:SS']);
}

$exibido_em_sql = $exibido_em->format('Y-m-d H:i:s');
$inserido_em_sql = date('Y-m-d H:i:s');

$telas = [];

$stmt_telas = $conn->prepare("SELECT id_tela FROM telas WHERE id_local = ?");

if (!$stmt_telas) {
    json_response(['erro' => 'Erro ao preparar consulta de telas: ' . $conn->error]);
}

$stmt_telas->bind_param("i", $id_local);
$stmt_telas->execute();
$result_telas = $stmt_telas->get_result();

while ($row = $result_telas->fetch_assoc()) {
    $telas[] = (int) $row['id_tela'];
}

$stmt_telas->close();

if (count($telas) === 0) {
    json_response(['erro' => 'Nenhuma tela encontrada para este local']);
}

$conn->begin_transaction();

$stmt_insert = $conn->prepare(
    "INSERT INTO publicidade_exibicao (id_local, id_tela, id_conteudo, exibido_em, inserido_em)
     VALUES (?, ?, ?, ?, ?)"
);

if (!$stmt_insert) {
    $conn->rollback();
    json_response(['erro' => 'Erro ao preparar insert de exibição: ' . $conn->error]);
}

$success = true;
$inserted_count = 0;
$id_tela = null;
$insert_error = '';

foreach ($telas as $tela) {
    $id_tela = $tela;
    $stmt_insert->bind_param("iiiss", $id_local, $id_tela, $id_conteudo, $exibido_em_sql, $inserido_em_sql);

    if (!$stmt_insert->execute()) {
        $success = false;
        $insert_error = $stmt_insert->error;
        break;
    }

    $inserted_count++;
}

$stmt_insert->close();

if (!$success) {
    $conn->rollback();
    json_response(['erro' => 'Falha ao inserir exibição: ' . $insert_error]);
}

$conn->commit();
$conn->close();

json_response([
    'success' => true,
    'inseridos' => $inserted_count,
    'id_local' => $id_local,
    'id_conteudo' => $id_conteudo,
    'exibido_em' => $exibido_em_sql,
    'inserido_em' => $inserido_em_sql
]);

?>
