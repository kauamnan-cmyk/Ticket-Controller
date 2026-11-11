<?php

ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
error_reporting(E_ALL);

header('Content-Type: application/json; charset=utf-8');

include __DIR__ . '/../conexao.php';

$conn->set_charset("utf8mb4");

$offline_after_minutes = 3;

function buscar_ids_para_evento($conn, $sql) {
    $result = $conn->query($sql);

    if (!$result) {
        throw new Exception($conn->error);
    }

    $ids = [];
    while ($row = $result->fetch_assoc()) {
        $ids[] = (int) $row['id_aparelho'];
    }

    return $ids;
}

function registrar_eventos($conn, $ids, $evento, $detalhe) {
    if (empty($ids)) {
        return;
    }

    $stmt = $conn->prepare("INSERT INTO aparelhos_eventos (id_aparelho, evento, detalhe) VALUES (?, ?, ?)");

    if (!$stmt) {
        throw new Exception($conn->error);
    }

    foreach ($ids as $id_aparelho) {
        $stmt->bind_param("iss", $id_aparelho, $evento, $detalhe);

        if (!$stmt->execute()) {
            throw new Exception($stmt->error);
        }
    }

    $stmt->close();
}

try {
    $conn->begin_transaction();

    $sql_ids_online = "SELECT id_aparelho
            FROM aparelhos_status
            WHERE ultimo_ping >= DATE_SUB(NOW(), INTERVAL {$offline_after_minutes} MINUTE)
            AND status <> 'online'
            FOR UPDATE";

    $sql_ids_offline = "SELECT id_aparelho
            FROM aparelhos_status
            WHERE ultimo_ping < DATE_SUB(NOW(), INTERVAL {$offline_after_minutes} MINUTE)
            AND status <> 'offline'
            FOR UPDATE";

    $ids_online = buscar_ids_para_evento($conn, $sql_ids_online);
    $ids_offline = buscar_ids_para_evento($conn, $sql_ids_offline);

    registrar_eventos(
        $conn,
        $ids_online,
        'online',
        'Aparelho voltou a responder dentro do limite de ping'
    );

    registrar_eventos(
        $conn,
        $ids_offline,
        'offline',
        "Aparelho sem ping ha mais de {$offline_after_minutes} minutos"
    );

    $sql_online = "UPDATE aparelhos_status
            SET status = 'online'
            WHERE ultimo_ping >= DATE_SUB(NOW(), INTERVAL {$offline_after_minutes} MINUTE)
            AND status <> 'online'";

    if (!$conn->query($sql_online)) {
        throw new Exception('Erro ao atualizar aparelhos online: ' . $conn->error);
    }

    $online_atualizados = $conn->affected_rows;

    $sql_offline = "UPDATE aparelhos_status
            SET status = 'offline'
            WHERE ultimo_ping < DATE_SUB(NOW(), INTERVAL {$offline_after_minutes} MINUTE)
            AND status <> 'offline'";

    if (!$conn->query($sql_offline)) {
        throw new Exception('Erro ao atualizar aparelhos offline: ' . $conn->error);
    }

    $offline_atualizados = $conn->affected_rows;
    $conn->commit();
} catch (Exception $e) {
    $conn->rollback();
    echo json_encode(['erro' => $e->getMessage()]) . PHP_EOL;
    $conn->close();
    exit(1);
}

echo json_encode([
    'success' => true,
    'offline_after_minutes' => $offline_after_minutes,
    'online_atualizados' => $online_atualizados,
    'offline_atualizados' => $offline_atualizados,
    'online_eventos' => count($ids_online),
    'offline_eventos' => count($ids_offline)
]) . PHP_EOL;

$conn->close();
?>
