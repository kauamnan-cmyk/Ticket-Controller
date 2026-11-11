<?php

function launcher_json_response($payload) {
    echo json_encode($payload, JSON_UNESCAPED_UNICODE);
    exit();
}

function launcher_error($message) {
    launcher_json_response([
        'success' => false,
        'erro' => $message
    ]);
}

function launcher_get_serial_param() {
    $serial = $_GET['serial_dispositivo'] ?? $_GET['serial'] ?? null;

    if ($serial === null || trim($serial) === '') {
        launcher_error('Parametro obrigatorio nao fornecido: serial_dispositivo');
    }

    return substr(trim($serial), 0, 120);
}

function launcher_resolver_dispositivo($conn, $serial_dispositivo) {
    $stmt_dispositivo = $conn->prepare(
        "SELECT id_dispositivo, serial_dispositivo
         FROM dispositivos
         WHERE serial_dispositivo = ?
         LIMIT 1"
    );

    if (!$stmt_dispositivo) {
        launcher_error('Erro na preparacao da consulta de dispositivo: ' . $conn->error);
    }

    $stmt_dispositivo->bind_param("s", $serial_dispositivo);
    $stmt_dispositivo->execute();
    $result_dispositivo = $stmt_dispositivo->get_result();

    if ($result_dispositivo->num_rows === 0) {
        $stmt_dispositivo->close();
        launcher_error('Dispositivo nao encontrado');
    }

    $dispositivo = $result_dispositivo->fetch_assoc();
    $stmt_dispositivo->close();

    $id_dispositivo = (int) $dispositivo['id_dispositivo'];

    if ($id_dispositivo <= 0) {
        launcher_error('Dispositivo invalido');
    }

    $stmt_local = $conn->prepare(
        "SELECT id_local
         FROM locais
         WHERE id_dispositivo = ?
         LIMIT 1"
    );

    if (!$stmt_local) {
        launcher_error('Erro na preparacao da consulta de local: ' . $conn->error);
    }

    $stmt_local->bind_param("i", $id_dispositivo);
    $stmt_local->execute();
    $result_local = $stmt_local->get_result();

    if ($result_local->num_rows === 0) {
        $stmt_local->close();
        launcher_error('Dispositivo sem local vinculado');
    }

    $local = $result_local->fetch_assoc();
    $stmt_local->close();

    $id_local = (int) $local['id_local'];

    if ($id_local <= 0) {
        launcher_error('Local vinculado invalido');
    }

    return [
        'serial_dispositivo' => $dispositivo['serial_dispositivo'],
        'id_dispositivo' => $id_dispositivo,
        'id_local' => $id_local
    ];
}

function launcher_request_origin() {
    $scheme = 'http';

    if (!empty($_SERVER['HTTP_X_FORWARDED_PROTO'])) {
        $scheme = strtolower(trim(explode(',', $_SERVER['HTTP_X_FORWARDED_PROTO'])[0]));
    } elseif (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off') {
        $scheme = 'https';
    }

    $host = $_SERVER['HTTP_HOST'] ?? 'example.com';
    return $scheme . '://' . $host;
}

function launcher_nextpubli_base_path() {
    $script_name = $_SERVER['SCRIPT_NAME'] ?? '';
    $marker = '/api/raspberry/';
    $marker_position = strpos($script_name, $marker);

    if ($marker_position !== false) {
        return rtrim(substr($script_name, 0, $marker_position), '/');
    }

    return '/nextpubli';
}

function launcher_public_url($path) {
    $path = trim((string) $path);

    if (preg_match('/^https?:\/\//i', $path)) {
        return $path;
    }

    $origin = launcher_request_origin();

    if (substr($path, 0, 1) === '/') {
        return $origin . $path;
    }

    return $origin . launcher_nextpubli_base_path() . '/' . ltrim($path, '/');
}

?>

