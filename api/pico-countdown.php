<?php

$config = include __DIR__ . '/../config/my.config.inc.php';

header('Content-Type: application/json');
header('Cache-Control: no-store, no-cache, must-revalidate, max-age=0');

$picture = $config['picture']['cntdwn_time'] ?? 5;
$collage = $config['collage']['cntdwn_time'] ?? 3;

echo json_encode([
    'picture_cntdwn_time' => (int)$picture,
    'collage_cntdwn_time' => (int)$collage,
]);
