<?php

declare(strict_types=1);

use Photobooth\Service\ConfigurationService;
use Photobooth\Utility\PathUtility;

require_once dirname(__DIR__) . '/lib/boot.php';

header('Content-Type: application/json');

try {
    $config = ConfigurationService::getInstance()->getConfiguration();

    if (empty($config['payments']['enabled'])) {
        echo json_encode([
            'status' => 'disabled',
            'error' => 'Payment system disabled',
        ]);
        exit;
    }

    $filename = trim((string)($_POST['filename'] ?? ''));
    $copies = (int)($_POST['copies'] ?? 1);

    if ($filename === '') {
        http_response_code(400);
        echo json_encode([
            'status' => 'error',
            'error' => 'Missing filename',
        ]);
        exit;
    }

    $provider = trim((string)($config['payments']['provider'] ?? 'none'));
    $paymentMode = trim((string)($config['payments']['payment_mode'] ?? ''));
    $legacyDisplayMode = trim((string)($config['payments']['display_mode'] ?? 'solo'));
    $webhookUrl = rtrim(trim((string)($config['payments']['webhook_url'] ?? '')), '/');

    if ($paymentMode === '') {
        $paymentMode = match ($legacyDisplayMode) {
            'qr' => 'qr',
            'both' => 'terminal_qr',
            default => 'terminal',
        };
    }

    $merchantCode = trim((string)($config['payments']['sumup']['merchant_code'] ?? ''));
    $readerId = trim((string)($config['payments']['sumup']['reader_id'] ?? ''));
    $affiliateKey = trim((string)($config['payments']['sumup']['affiliate_key'] ?? ''));

    $coinPicoUrl = rtrim(trim((string)($config['payments']['coin']['pico_url'] ?? '')), '/');
    $coinSecret = trim((string)($config['payments']['coin']['secret'] ?? ''));

    $amountCentsRaw = $config['payments']['price_cents'] ?? 0;
    $amountCents = (int)$amountCentsRaw;

    $python = '/usr/bin/python3';
    $soloScript = PathUtility::getAbsolutePath('api/sumup_solo.py');
    $checkoutScript = PathUtility::getAbsolutePath('api/create_checkout.py');

    $logFile = PathUtility::getAbsolutePath('private/payment-print.log');
    $jobFile = PathUtility::getAbsolutePath('private/photobooth_current_print.json');
    $soloBgLog = '/tmp/sumup_solo_both.log';
    $paymentMessageTemplate = trim((string)($config['payments']['message'] ?? 'Bitte zahlen Sie %price% €'));
    $formattedPrice = number_format($amountCents / 100, 2, '.', '');
    $coinStartMessage = str_replace('%price%', $formattedPrice, $paymentMessageTemplate);

    $logLines = [
        '[' . date('c') . '] startPaymentPrint',
        'filename=' . $filename,
        'copies=' . $copies,
        'provider=' . $provider,
        'payment_mode=' . $paymentMode,
        'legacy_display_mode=' . $legacyDisplayMode,
        'merchant_code=' . $merchantCode,
        'reader_id=' . $readerId,
        'affiliate_key_present=' . ($affiliateKey !== '' ? 'yes' : 'no'),
        'amount_cents=' . $amountCents,
        'webhook_url=' . $webhookUrl,
        'coin_pico_url=' . $coinPicoUrl,
        'coin_secret_present=' . ($coinSecret !== '' ? 'yes' : 'no'),
    ];

    if (!in_array($provider, ['sumup', 'coin', 'sumup_coin'], true)) {
        http_response_code(500);
        echo json_encode([
            'status' => 'error',
            'error' => 'Unsupported payment provider',
        ]);
        exit;
    }

    if ($amountCents <= 0) {
        http_response_code(500);
        echo json_encode([
            'status' => 'error',
            'error' => 'Price (cents) is invalid or missing',
        ]);
        exit;
    }

    $allowedModes = ['terminal', 'qr', 'terminal_qr', 'coin', 'terminal_coin', 'qr_coin', 'terminal_qr_coin'];
    if (!in_array($paymentMode, $allowedModes, true)) {
        http_response_code(500);
        echo json_encode([
            'status' => 'error',
            'error' => 'Payment mode not yet implemented',
        ]);
        exit;
    }

    $usesCoin = in_array($paymentMode, ['coin', 'terminal_coin', 'qr_coin', 'terminal_qr_coin'], true);
    $usesQr = in_array($paymentMode, ['qr', 'terminal_qr', 'qr_coin', 'terminal_qr_coin'], true);
    $usesTerminal = in_array($paymentMode, ['terminal', 'terminal_qr', 'terminal_coin', 'terminal_qr_coin'], true);
    $terminalSynchronous = ($paymentMode === 'terminal');

    if ($usesCoin && !in_array($provider, ['coin', 'sumup_coin'], true)) {
        http_response_code(500);
        echo json_encode([
            'status' => 'error',
            'error' => 'Payment provider does not allow coin mode',
        ]);
        exit;
    }

    if (($usesQr || $usesTerminal) && !in_array($provider, ['sumup', 'sumup_coin'], true)) {
        http_response_code(500);
        echo json_encode([
            'status' => 'error',
            'error' => 'Payment provider is not compatible with SumUp mode',
        ]);
        exit;
    }

    if (($usesQr || $usesTerminal) && $merchantCode === '') {
        http_response_code(500);
        echo json_encode([
            'status' => 'error',
            'error' => 'SumUp Merchant Code missing',
        ]);
        exit;
    }

    if ($usesCoin) {
        if ($coinPicoUrl === '') {
            http_response_code(500);
            echo json_encode([
                'status' => 'error',
                'error' => 'Coin Pico URL missing',
            ]);
            exit;
        }

        if ($coinSecret === '') {
            http_response_code(500);
            echo json_encode([
                'status' => 'error',
                'error' => 'Coin secret missing',
            ]);
            exit;
        }
    }

    if ($usesTerminal) {
        if ($readerId === '') {
            http_response_code(500);
            echo json_encode([
                'status' => 'error',
                'error' => 'SumUp Reader ID missing',
            ]);
            exit;
        }

        if ($affiliateKey === '') {
            http_response_code(500);
            echo json_encode([
                'status' => 'error',
                'error' => 'SumUp Affiliate Key missing',
            ]);
            exit;
        }

        if (!is_file($soloScript)) {
            http_response_code(500);
            echo json_encode([
                'status' => 'error',
                'error' => 'sumup_solo.py not found',
            ]);
            exit;
        }
    }

    if ($usesQr) {
        if ($webhookUrl === '') {
            http_response_code(500);
            echo json_encode([
                'status' => 'error',
                'error' => 'ngrok URL / webhook_url missing',
            ]);
            exit;
        }

        if (!is_file($checkoutScript)) {
            http_response_code(500);
            echo json_encode([
                'status' => 'error',
                'error' => 'create_checkout.py not found',
            ]);
            exit;
        }
    }

    $writeJob = static function (
        string $jobFile,
        string $filename,
        int $copies,
        string $provider,
        string $paymentMode,
        int $amountCents
    ): int|false {
        $jobData = json_encode([
            'filename' => $filename,
            'copies' => $copies,
            'printed' => false,
            'paid' => false,
            'provider' => $provider,
            'payment_mode' => $paymentMode,
            'payment_channel' => $paymentMode,
            'amount_cents_due' => $amountCents,
            'amount_cents_received' => 0,
            'created_at' => date('c'),
        ], JSON_UNESCAPED_SLASHES | JSON_PRETTY_PRINT);

        return file_put_contents($jobFile, $jobData);
    };

    $writeLog = static function (string $logFile, array $lines): void {
        file_put_contents($logFile, implode(PHP_EOL, $lines) . PHP_EOL . PHP_EOL, FILE_APPEND);
    };

    // Pure terminal mode keeps the old synchronous behaviour.
    if ($terminalSynchronous) {
        $cmd = escapeshellcmd($python) . ' ' .
            escapeshellarg($soloScript) . ' ' .
            escapeshellarg($merchantCode) . ' ' .
            escapeshellarg($readerId) . ' ' .
            escapeshellarg($affiliateKey) . ' ' .
            escapeshellarg((string)$amountCents) . ' 2>&1';

        $output = [];
        $returnVar = 1;
        exec($cmd, $output, $returnVar);

        $logLines[] = 'command=' . $cmd;
        $logLines[] = 'return_code=' . $returnVar;
        $logLines[] = 'output:';
        $logLines[] = implode(PHP_EOL, $output);

        $writeLog($logFile, $logLines);

        if ($returnVar === 0) {
            echo json_encode([
                'status' => 'success',
                'provider' => $provider,
                'payment_mode' => $paymentMode,
                'message' => 'Payment successful - printing starts...',
            ]);
            exit;
        }

        echo json_encode([
            'status' => 'error',
            'error' => 'Payment failed or was cancelled',
            'log' => implode("\n", $output),
        ]);
        exit;
    }

    $jobWriteResult = $writeJob($jobFile, $filename, $copies, $provider, $paymentMode, $amountCents);
    $logLines[] = 'job_file=' . $jobFile;
    $logLines[] = 'job_write_result=' . var_export($jobWriteResult, true);

    $paymentUrl = '';

    if ($usesQr) {
        $returnUrl = $webhookUrl . '/sumup/webhook';

        $checkoutCmd = escapeshellcmd($python) . ' ' .
            escapeshellarg($checkoutScript) . ' ' .
            escapeshellarg($merchantCode) . ' ' .
            escapeshellarg((string)$amountCents) . ' ' .
            escapeshellarg($returnUrl) . ' 2>&1';

        $checkoutOutput = [];
        $checkoutReturnVar = 1;
        exec($checkoutCmd, $checkoutOutput, $checkoutReturnVar);

        if (!empty($checkoutOutput)) {
            $paymentUrl = trim(end($checkoutOutput));
        }

        $logLines[] = 'checkout_command=' . $checkoutCmd;
        $logLines[] = 'checkout_return_code=' . $checkoutReturnVar;
        $logLines[] = 'checkout_output:';
        $logLines[] = implode(PHP_EOL, $checkoutOutput);
        $logLines[] = 'payment_url=' . $paymentUrl;

        if ($checkoutReturnVar !== 0 || $paymentUrl === '' || strpos($paymentUrl, 'https://') !== 0) {
            $writeLog($logFile, $logLines);

            http_response_code(500);
            echo json_encode([
                'status' => 'error',
                'error' => 'The QR payment link could not be generated.',
                'log' => implode("\n", $checkoutOutput),
            ]);
            exit;
        }
    }

    if ($usesCoin) {
        $coinPayload = json_encode([
            'secret' => $coinSecret,
            'amount_cents' => $amountCents,
            'message' => $coinStartMessage,
        ], JSON_UNESCAPED_SLASHES);

        $coinContext = stream_context_create([
            'http' => [
                'method' => 'POST',
                'header' => "Content-Type: application/json\r\n",
                'content' => $coinPayload,
                'timeout' => 5,
                'ignore_errors' => true,
            ],
        ]);

        $coinResponse = @file_get_contents($coinPicoUrl, false, $coinContext);
        $httpStatusLine = $http_response_header[0] ?? '';
        $coinStartOk = is_string($httpStatusLine) && preg_match('/\s2\d\d\s/', $httpStatusLine) === 1;

        $logLines[] = 'coin_request_url=' . $coinPicoUrl;
        $logLines[] = 'coin_request_payload=' . $coinPayload;
        $logLines[] = 'coin_response_status=' . $httpStatusLine;
        $logLines[] = 'coin_response_body=' . (is_string($coinResponse) ? $coinResponse : '');

        if (!$coinStartOk) {
            $writeLog($logFile, $logLines);

            http_response_code(500);
            echo json_encode([
                'status' => 'error',
                'error' => 'Coin payment could not be started',
                'details' => is_string($coinResponse) ? $coinResponse : '',
            ]);
            exit;
        }
    }

    if ($usesTerminal && !$terminalSynchronous) {
        $soloCmd = 'nohup ' .
            escapeshellcmd($python) . ' ' .
            escapeshellarg($soloScript) . ' ' .
            escapeshellarg($merchantCode) . ' ' .
            escapeshellarg($readerId) . ' ' .
            escapeshellarg($affiliateKey) . ' ' .
            escapeshellarg((string)$amountCents) .
            ' >> ' . escapeshellarg($soloBgLog) . ' 2>&1 &';

        exec($soloCmd);
        $logLines[] = 'solo_background_command=' . $soloCmd;
    }

    $writeLog($logFile, $logLines);

    switch ($paymentMode) {
        case 'coin':
            echo json_encode([
                'status' => 'coin',
                'provider' => $provider,
                'payment_mode' => $paymentMode,
                'message' => 'Coin payment ready',
            ]);
            exit;

        case 'qr':
            echo json_encode([
                'status' => 'qr',
                'provider' => $provider,
                'payment_mode' => $paymentMode,
                'payment_url' => $paymentUrl,
                'message' => 'QR payment ready',
            ]);
            exit;

        case 'terminal_qr':
            echo json_encode([
                'status' => 'both',
                'provider' => $provider,
                'payment_mode' => $paymentMode,
                'payment_url' => $paymentUrl,
                'message' => 'QR payment ready, Terminal started in background',
            ]);
            exit;

        case 'terminal_coin':
            echo json_encode([
                'status' => 'coin',
                'provider' => $provider,
                'payment_mode' => $paymentMode,
                'message' => 'Coin payment ready, Terminal started in background',
            ]);
            exit;

        case 'qr_coin':
            echo json_encode([
                'status' => 'qr',
                'provider' => $provider,
                'payment_mode' => $paymentMode,
                'payment_url' => $paymentUrl,
                'message' => 'QR payment ready, Coin enabled',
            ]);
            exit;

        case 'terminal_qr_coin':
            echo json_encode([
                'status' => 'both',
                'provider' => $provider,
                'payment_mode' => $paymentMode,
                'payment_url' => $paymentUrl,
                'message' => 'QR payment ready, Terminal started in background, Coin enabled',
            ]);
            exit;
    }

    http_response_code(500);
    echo json_encode([
        'status' => 'error',
        'error' => 'Invalid payment method',
    ]);
} catch (\Throwable $e) {
    http_response_code(500);

    $logFile = PathUtility::getAbsolutePath('private/payment-print.log');
    file_put_contents(
        $logFile,
        '[' . date('c') . '] EXCEPTION startPaymentPrint: ' . $e->getMessage() . PHP_EOL,
        FILE_APPEND
    );

    echo json_encode([
        'status' => 'error',
        'error' => $e->getMessage(),
    ]);
}
