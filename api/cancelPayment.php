<?php

declare(strict_types=1);

use Photobooth\Utility\PathUtility;

require_once dirname(__DIR__) . '/lib/boot.php';

header('Content-Type: application/json');

$jobFile = PathUtility::getAbsolutePath('private/photobooth_current_print.json');

if (!is_file($jobFile)) {
    echo json_encode([
        'status' => 'missing',
        'cancelled' => false,
    ]);
    exit;
}

$data = json_decode((string)file_get_contents($jobFile), true);

if (!is_array($data)) {
    http_response_code(500);
    echo json_encode([
        'status' => 'invalid',
        'cancelled' => false,
    ]);
    exit;
}

$data['paid'] = false;
$data['printed'] = false;
$data['cancelled'] = true;
$data['cancelled_at'] = date('c');

$result = file_put_contents(
    $jobFile,
    json_encode($data, JSON_UNESCAPED_SLASHES | JSON_PRETTY_PRINT)
);

if ($result === false) {
    http_response_code(500);
    echo json_encode([
        'status' => 'error',
        'cancelled' => false,
    ]);
    exit;
}

echo json_encode([
    'status' => 'cancelled',
    'cancelled' => true,
]);
