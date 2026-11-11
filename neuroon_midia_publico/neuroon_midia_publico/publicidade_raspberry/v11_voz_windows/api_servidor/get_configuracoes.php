<?php

ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
error_reporting(E_ALL);

header('Content-Type: application/json; charset=utf-8');

$id_local_param = $_GET['id_local'] ?? $_GET['id_tela'] ?? $_GET['id'] ?? null;

if ($id_local_param === null || $id_local_param === '') {
    echo json_encode(['success' => false, 'erro' => 'ID do local nao fornecido']);
    exit();
}

$configuracoes = [
    'api_publicidade_check_interval_ms' => 10000,
    'api_informativo_check_interval_ms' => 300000,
    'api_posicao_tela_check_interval_ms' => 60000,
    'api_ping_aparelho_interval_ms' => 60000,
    'api_senhas_chamada_interval_ms' => 3000,
    'senhas_chamada_fullscreen_timeout_ms' => 600000,
    'image_display_time_ms' => 10000,
    'informativo_display_time_ms' => 120000,
    'datetime_update_interval_ms' => 1000,
    'report_interval_ms' => 60000,
    'font_size_titulo' => 24,
    'font_size_subtitulo' => 18,
    'font_size_texto' => 14,
    'font_size_aviso' => 24,
    'font_size_icon' => 20,
];

echo json_encode([
    'success' => true,
    'id_local' => (int) $id_local_param,
    'configuracoes' => $configuracoes,
]);

?>
