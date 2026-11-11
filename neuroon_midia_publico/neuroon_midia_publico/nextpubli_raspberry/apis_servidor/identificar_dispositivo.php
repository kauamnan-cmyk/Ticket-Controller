<?php

ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
error_reporting(E_ALL);

header('Content-Type: application/json; charset=utf-8');

include __DIR__ . '/../conexao.php';
include __DIR__ . '/launcher_helpers.php';

$conn->set_charset("utf8mb4");

$serial_dispositivo = launcher_get_serial_param();
$identity = launcher_resolver_dispositivo($conn, $serial_dispositivo);

launcher_json_response([
    'success' => true,
    'serial_dispositivo' => $identity['serial_dispositivo'],
    'id_dispositivo' => $identity['id_dispositivo'],
    'id_local' => $identity['id_local']
]);

$conn->close();
?>

