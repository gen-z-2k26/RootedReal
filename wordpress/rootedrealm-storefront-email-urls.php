<?php
/**
 * Rewrite WordPress links in emails to the public storefront.
 * Paste into Snippets and replace any previous wcf_ca-only snippet.
 * Leave wp-content, wp-admin, and wp-json on wp.rootedrealm.com so images still load.
 */

function rootedrealm_storefront_rewrite_url($url) {
    if (!is_string($url) || $url === '') {
        return $url;
    }

    if (!preg_match('#^https?://wp\.rootedrealm\.com(/.*)?$#i', $url, $parts)) {
        return $url;
    }

    $path = isset($parts[1]) ? $parts[1] : '';
    if ($path && preg_match('#^/(wp-content|wp-admin|wp-includes|wp-json|xmlrpc)#i', $path)) {
        return $url;
    }

    $path = preg_replace('#^/product/#', '/products/', $path);
    $path = preg_replace('#^/shop/?$#', '/products', $path);
    $path = preg_replace('#^/cart/?$#', '/cart', $path);

    return 'https://www.rootedrealm.com' . $path;
}

function rootedrealm_storefront_rewrite_text($text) {
    if (!is_string($text) || $text === '') {
        return $text;
    }

    return preg_replace_callback(
        '#https?://wp\.rootedrealm\.com[^\s"\'<>]*#i',
        function ($match) {
            return rootedrealm_storefront_rewrite_url($match[0]);
        },
        $text
    );
}

add_filter('wcf_ca_email_body_before_send', 'rootedrealm_storefront_rewrite_text', 20);
add_filter('woocommerce_mail_content', 'rootedrealm_storefront_rewrite_text', 20);

add_filter('wp_mail', function ($args) {
    if (!empty($args['message'])) {
        $args['message'] = rootedrealm_storefront_rewrite_text($args['message']);
    }
    if (!empty($args['subject'])) {
        $args['subject'] = rootedrealm_storefront_rewrite_text($args['subject']);
    }
    return $args;
}, 20);

add_action('phpmailer_init', function ($phpmailer) {
    if (!empty($phpmailer->Body)) {
        $phpmailer->Body = rootedrealm_storefront_rewrite_text($phpmailer->Body);
    }
    if (!empty($phpmailer->AltBody)) {
        $phpmailer->AltBody = rootedrealm_storefront_rewrite_text($phpmailer->AltBody);
    }
}, 20);
