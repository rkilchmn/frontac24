<?php
/**
 * phpMyAdmin auto-login page
 * Served at /phpmyadmin/ - auto-submits login form with credentials from .env
 */

$host = getenv('PMA_HOST') ?: 'db';
$port = getenv('PMA_PORT') ?: '3306';
$user = getenv('PMA_USER') ?: 'frontacc';
$pass = getenv('PMA_PASSWORD') ?: '';
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>phpMyAdmin - FrontAccounting</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f6f7; 
            min-height: 100vh; 
            display: flex; 
            align-items: center; 
            justify-content: center; 
        }
        .container {
            background: white;
            padding: 2rem;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            width: 100%;
            max-width: 400px;
        }
        .logo { text-align: center; margin-bottom: 1.5rem; }
        .logo img { max-width: 120px; }
        h1 { font-size: 1.5rem; color: #333; margin-bottom: 0.5rem; text-align: center; }
        .subtitle { color: #666; text-align: center; margin-bottom: 2rem; }
        .info { 
            background: #e8f5e9; 
            border: 1px solid #c8e6c9; 
            border-radius: 4px; 
            padding: 1rem; 
            margin-bottom: 1.5rem; 
            font-size: 0.9rem; 
        }
        .info strong { color: #2e7d32; }
        .btn {
            width: 100%;
            padding: 0.75rem;
            background: #0066cc;
            color: white;
            border: none;
            border-radius: 4px;
            font-size: 1rem;
            cursor: pointer;
            transition: background 0.2s;
        }
        .btn:hover { background: #0052a3; }
        .spinner {
            display: none;
            width: 20px; height: 20px;
            border: 3px solid #f3f3f3;
            border-top: 3px solid #0066cc;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .btn.loading .btn-text { display: none; }
        .btn.loading .spinner { display: block; }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">
            <svg width="120" height="120" viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect width="120" height="120" rx="16" fill="#0066cc"/>
                <text x="60" y="80" font-family="Arial, sans-serif" font-size="48" font-weight="bold" fill="white" text-anchor="middle">PMA</text>
            </svg>
        </div>
        <h1>phpMyAdmin</h1>
        <p class="subtitle">FrontAccounting Database</p>
        
        <div class="info">
            <strong>Auto-login enabled</strong><br>
            Host: <?= htmlspecialchars($host) ?>:<?= htmlspecialchars($port) ?><br>
            User: <?= htmlspecialchars($user) ?>
        </div>

        <form id="loginForm" action="/phpmyadmin/" method="post">
            <input type="hidden" name="server" value="1">
            <input type="hidden" name="lang" value="en">
            <input type="hidden" name="collation_connection" value="utf8mb4_general_ci">
            <input type="hidden" name="username" value="<?= htmlspecialchars($user) ?>">
            <input type="hidden" name="password" value="<?= htmlspecialchars($pass) ?>">
            <input type="hidden" name="target" value="index.php">
            <input type="hidden" name="token" value="">
            <button type="submit" class="btn" id="submitBtn">
                <span class="btn-text">Opening phpMyAdmin...</span>
                <span class="spinner"></span>
            </button>
        </form>

        <script>
            // Auto-submit after a brief moment
            setTimeout(() => {
                document.getElementById('submitBtn').classList.add('loading');
                document.getElementById('loginForm').submit();
            }, 500);
        </script>
    </div>
</body>
</html>