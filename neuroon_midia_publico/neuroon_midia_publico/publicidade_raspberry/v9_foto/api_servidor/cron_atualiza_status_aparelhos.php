<?php

ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
error_reporting(E_ALL);

if (PHP_SAPI !== 'cli') {
    http_response_code(403);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode(['erro' => 'Este script deve ser executado via cron/CLI']);
    exit();
}

include __DIR__ . '/../conexao.php';

$conn->set_charset("utf8mb4");

$offline_after_minutes = 3;

$sql_online = "UPDATE aparelhos_status
        SET status = 'online'
        WHERE ultimo_ping >= DATE_SUB(NOW(), INTERVAL {$offline_after_minutes} MINUTE)
        AND status <> 'online'";

$sql_offline = "UPDATE aparelhos_status
        SET status = 'offline'
        WHERE ultimo_ping < DATE_SUB(NOW(), INTERVAL {$offline_after_minutes} MINUTE)
        AND status <> 'offline'";

if (!$conn->query($sql_online)) {
    echo json_encode(['erro' => 'Erro ao atualizar aparelhos online: ' . $conn->error]) . PHP_EOL;
    $conn->close();
    exit(1);
}

$online_atualizados = $conn->affected_rows;

if (!$conn->query($sql_offline)) {
    echo json_encode(['erro' => 'Erro ao atualizar aparelhos offline: ' . $conn->error]) . PHP_EOL;
    $conn->close();
    exit(1);
}

$offline_atualizados = $conn->affected_rows;

echo json_encode([
    'success' => true,
    'offline_after_minutes' => $offline_after_minutes,
    'online_atualizados' => $online_atualizados,
    'offline_atualizados' => $offline_atualizados
]) . PHP_EOL;

$conn->close();
?>
