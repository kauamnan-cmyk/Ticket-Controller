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

$stmt_local = $conn->prepare("SELECT id_dispositivo FROM locais WHERE id_local = ? LIMIT 1");

if (!$stmt_local) {
    echo json_encode(['erro' => 'Erro na preparacao da consulta de local: ' . $conn->error]);
    exit();
}

$stmt_local->bind_param("i", $id_local);
$stmt_local->execute();
$result_local = $stmt_local->get_result();

if ($result_local->num_rows === 0) {
    echo json_encode(['erro' => 'Local nao encontrado']);
    $stmt_local->close();
    $conn->close();
    exit();
}

$local = $result_local->fetch_assoc();
$id_dispositivo = (int) $local['id_dispositivo'];
$stmt_local->close();

if ($id_dispositivo <= 0) {
    echo json_encode(['erro' => 'Local sem dispositivo vinculado']);
    $conn->close();
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

try {
    $conn->begin_transaction();

    $status_anterior = null;
    $aparelho_existente = false;

    $stmt_select = $conn->prepare("SELECT status FROM aparelhos_status WHERE id_aparelho = ? FOR UPDATE");

    if (!$stmt_select) {
        throw new Exception('Erro na preparacao da consulta: ' . $conn->error);
    }

    $stmt_select->bind_param("i", $id_dispositivo);

    if (!$stmt_select->execute()) {
        throw new Exception('Erro ao consultar status anterior: ' . $stmt_select->error);
    }

    $stmt_select->store_result();
    $aparelho_existente = $stmt_select->num_rows > 0;

    if ($aparelho_existente) {
        $stmt_select->bind_result($status_anterior);
        $stmt_select->fetch();
    }

    $stmt_select->close();

    if ($aparelho_existente) {
        $stmt_status = $conn->prepare(
            "UPDATE aparelhos_status
             SET ultimo_ping = NOW(),
                 status = 'online',
                 ip = ?,
                 versao_app = ?,
                 atualizado_em = CURRENT_TIMESTAMP
             WHERE id_aparelho = ?"
        );

        if (!$stmt_status) {
            throw new Exception('Erro na preparacao do update: ' . $conn->error);
        }

        $stmt_status->bind_param("ssi", $ip, $versao_app, $id_dispositivo);
    } else {
        $stmt_status = $conn->prepare(
            "INSERT INTO aparelhos_status (id_aparelho, ultimo_ping, status, ip, versao_app)
             VALUES (?, NOW(), 'online', ?, ?)"
        );

        if (!$stmt_status) {
            throw new Exception('Erro na preparacao do insert: ' . $conn->error);
        }

        $stmt_status->bind_param("iss", $id_dispositivo, $ip, $versao_app);
    }

    if (!$stmt_status->execute()) {
        throw new Exception('Erro ao registrar ping: ' . $stmt_status->error);
    }

    $stmt_status->close();

    $evento_registrado = false;

    if (!$aparelho_existente || $status_anterior !== 'online') {
        $evento = 'online';
        $detalhe = $aparelho_existente
            ? 'Aparelho voltou a responder apos status ' . $status_anterior
            : 'Primeiro ping registrado';

        $stmt_evento = $conn->prepare(
            "INSERT INTO aparelhos_eventos (id_aparelho, evento, detalhe) VALUES (?, ?, ?)"
        );

        if (!$stmt_evento) {
            throw new Exception('Erro na preparacao do evento: ' . $conn->error);
        }

        $stmt_evento->bind_param("iss", $id_dispositivo, $evento, $detalhe);

        if (!$stmt_evento->execute()) {
            throw new Exception('Erro ao registrar evento: ' . $stmt_evento->error);
        }

        $stmt_evento->close();
        $evento_registrado = true;
    }

    $conn->commit();

    echo json_encode([
        'success' => true,
        'mensagem' => 'Ping registrado com sucesso',
        'id_local' => $id_local,
        'id_dispositivo' => $id_dispositivo,
        'evento_registrado' => $evento_registrado
    ]);
} catch (Exception $e) {
    $conn->rollback();
    echo json_encode(['erro' => $e->getMessage()]);
}

$conn->close();
?>
