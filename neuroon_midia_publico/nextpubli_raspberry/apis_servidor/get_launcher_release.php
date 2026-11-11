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

$stmt_release = $conn->prepare(
    "SELECT id_release, version, package_path, package_sha256, entrypoint
     FROM raspberry_releases
     WHERE status = 'published'
     AND is_active = 1
     ORDER BY published_at DESC, id_release DESC
     LIMIT 1"
);

if (!$stmt_release) {
    launcher_error('Erro na preparacao da consulta de release: ' . $conn->error);
}

$stmt_release->execute();
$result_release = $stmt_release->get_result();

if ($result_release->num_rows === 0) {
    $stmt_release->close();
    launcher_error('Nenhuma release ativa publicada');
}

$release = $result_release->fetch_assoc();
$stmt_release->close();

if (
    empty($release['version']) ||
    empty($release['package_path']) ||
    empty($release['package_sha256']) ||
    empty($release['entrypoint'])
) {
    launcher_error('Release ativa com metadados incompletos');
}

$id_release = (int) $release['id_release'];

$stmt_scripts = $conn->prepare(
    "SELECT name, script_path, script_sha256, run_as
     FROM raspberry_release_scripts
     WHERE id_release = ?
     AND is_enabled = 1
     ORDER BY execution_order ASC, id_script ASC"
);

if (!$stmt_scripts) {
    launcher_error('Erro na preparacao da consulta de scripts: ' . $conn->error);
}

$stmt_scripts->bind_param("i", $id_release);
$stmt_scripts->execute();
$result_scripts = $stmt_scripts->get_result();

$scripts = [];
while ($script = $result_scripts->fetch_assoc()) {
    if (
        empty($script['name']) ||
        empty($script['script_path']) ||
        empty($script['script_sha256']) ||
        !in_array($script['run_as'], ['user', 'sudo'], true)
    ) {
        $stmt_scripts->close();
        launcher_error('Release ativa possui script com metadados invalidos');
    }

    $scripts[] = [
        'name' => $script['name'],
        'url' => launcher_public_url($script['script_path']),
        'sha256' => strtolower($script['script_sha256']),
        'run_as' => $script['run_as']
    ];
}

$stmt_scripts->close();

launcher_json_response([
    'success' => true,
    'serial_dispositivo' => $identity['serial_dispositivo'],
    'id_dispositivo' => $identity['id_dispositivo'],
    'id_local' => $identity['id_local'],
    'version' => $release['version'],
    'package_url' => launcher_public_url($release['package_path']),
    'package_sha256' => strtolower($release['package_sha256']),
    'entrypoint' => $release['entrypoint'],
    'scripts' => $scripts
]);

$conn->close();
?>

