import express from 'express';
import type { Request, Response } from 'express';
import { Client, LocalAuth, MessageMedia } from 'whatsapp-web.js';
import qrcode from 'qrcode-terminal';
import cors from 'cors';
import dotenv from 'dotenv';

dotenv.config();

function parseEnvList(name: string): string[] {
  const value = process.env[name] ?? '';
  return value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);
}

function normalizeGroupName(name: string): string {
  return name.normalize('NFKC').replace(/\s+/g, ' ').trim().toLowerCase();
}

/**
 * Express app configuration
 * - Enables CORS
 * - Allows JSON bodies up to 10 MB (used for base64-encoded images)
 */
const app = express();
app.use(cors());
app.use(express.json({ limit: '10mb' }));

/**
 * @constant targetGroups
 * @description List of WhatsApp group names where messages will be sent.
 *              The bot will cache these groups on startup and only send messages to them.
 * @example ["Deals Group", "Promo Watchers"]
 */
const targetGroups = parseEnvList('WHATSAPP_TARGET_GROUPS');

/**
 * @constant groupsCache
 * @description Caches the IDs of target WhatsApp groups after client initialization,
 *              avoiding repeated lookups or API calls.
 */
let groupsCache: { name: string; id: string }[] = [];

/**
 * @constant client
 * @description WhatsApp client configured with local authentication (stores session on disk).
 *              Puppeteer is launched in sandbox-free mode for compatibility with minimal environments.
 */
const client = new Client({
  authStrategy: new LocalAuth(),
  puppeteer: {
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  },
});

process.on('unhandledRejection', (reason) => {
  console.error('🧪 DEBUG unhandledRejection:', reason);
});

process.on('uncaughtException', (error) => {
  console.error('🧪 DEBUG uncaughtException:', error);
});

const internalClient = client as any;
const originalInject = internalClient.inject.bind(client);
internalClient.inject = (async (...args: any[]) => {
  const page = internalClient.pupPage;
  console.log('🧪 DEBUG inject:start', {
    hasPage: Boolean(page),
    url: page?.url?.() ?? 'unavailable',
  });

  try {
    const result = await originalInject(...args);
    console.log('🧪 DEBUG inject:success', {
      url: page?.url?.() ?? 'unavailable',
    });
    return result;
  } catch (error) {
    let readyState = 'unavailable';
    let title = 'unavailable';

    if (page) {
      try {
        readyState = await page.evaluate(() => document.readyState);
      } catch (evaluateError) {
        readyState = `evaluate_failed: ${String(evaluateError)}`;
      }

      try {
        title = await page.title();
      } catch (titleError) {
        title = `title_failed: ${String(titleError)}`;
      }
    }

    console.error('🧪 DEBUG inject:error', {
      error,
      url: page?.url?.() ?? 'unavailable',
      readyState,
      title,
    });
    throw error;
  }
}) as typeof originalInject;

/**
 * QR Code event handler
 * Triggered when WhatsApp Web needs a new authentication QR code.
 * Displays a small QR code directly in the terminal for convenience.
 */
client.on('qr', (qr: string) => {
  console.log('📱 QR CODE RECEIVED — scan it with WhatsApp:');
  qrcode.generate(qr, { small: true });
});

client.on('authenticated', () => {
  console.log('🔐 WhatsApp session authenticated.');
});

client.on('auth_failure', (message: string) => {
  console.error('❌ WhatsApp auth failure:', message);
});

client.on('loading_screen', (percent: string | number, message: string) => {
  console.log(`⏳ WhatsApp loading: ${percent}% - ${message}`);
});

client.on('disconnected', (reason: string) => {
  console.warn('⚠️ WhatsApp disconnected:', reason);
});

client.on('change_state', (state: string) => {
  console.log('🧪 DEBUG change_state:', state);
});

/**
 * Ready event handler
 * Fired once the WhatsApp client has successfully authenticated and connected.
 * The bot caches the target group IDs so that message dispatch can be fast and efficient.
 */
client.on('ready', async () => {
  console.log('✅ WhatsApp client is ready and authenticated.');
  const chats = await client.getChats();
  const normalizedTargets = new Set(targetGroups.map(normalizeGroupName));

  // Filter and cache only the target groups specified in targetGroups[]
  groupsCache = chats
    .filter((c) => c.isGroup && normalizedTargets.has(normalizeGroupName(c.name)))
    .map((c) => ({ name: c.name, id: c.id._serialized }));

  console.log('📋 Cached groups:');
  groupsCache.forEach((g) => console.log(`- ${g.name}`));
  if (groupsCache.length === 0) {
    console.warn('⚠️ No matching WhatsApp groups were found for WHATSAPP_TARGET_GROUPS.');
    console.log('📚 Available WhatsApp groups seen by the session:');
    chats
      .filter((c) => c.isGroup)
      .map((c) => c.name)
      .sort((a, b) => a.localeCompare(b))
      .forEach((name) => console.log(`- ${name}`));
  }
});

/**
 * Sends messages (text and optionally image) to all cached WhatsApp groups.
 * Each send operation is delayed slightly (1 second) to avoid being flagged as spam.
 *
 * @param text - The text message to send.
 * @param base64Image - Optional base64-encoded image.
 * @param mimeType - Optional MIME type (e.g. 'image/jpeg').
 */
async function sendToGroups(text: string, base64Image?: string, mimeType?: string) {
  if (groupsCache.length === 0) {
    throw new Error('No WhatsApp groups are currently cached.');
  }

  let successCount = 0;
  const failures: { group: string; error: string }[] = [];

  for (const group of groupsCache) {
    try {
      if (base64Image && mimeType?.startsWith('image/')) {
        // Send message with image attachment
        const media = new MessageMedia(mimeType, base64Image);
        await client.sendMessage(group.id, media, { caption: text });
      } else {
        // Send plain text message
        await client.sendMessage(group.id, text);
      }
      console.log(`📤 Message successfully sent to ${group.name}`);
      successCount += 1;
    } catch (err: any) {
      console.error(`❌ Error sending to ${group.name}:`, err);
      failures.push({
        group: group.name,
        error: err instanceof Error ? err.message : String(err),
      });
    }

    // Wait 1s between sends to reduce risk of being flagged
    await new Promise((resolve) => setTimeout(resolve, 1000));
  }

  if (successCount === 0) {
    throw new Error(`Failed to send message to every configured WhatsApp group: ${JSON.stringify(failures)}`);
  }

  return {
    successCount,
    failureCount: failures.length,
    failures,
  };
}

/**
 * POST /send
 * --------------------------------------
 * Public API endpoint used to send a message (and optionally an image)
 * to all the groups in `targetGroups`.
 *
 * Expected JSON body:
 * ```json
 * {
 *   "text": "Your message content",
 *   "base64Image": "<optional base64 string>",
 *   "mimeType": "image/jpeg"
 * }
 * ```
 */
app.post('/send', async (req: Request, res: Response) => {
  const { text, base64Image, mimeType } = req.body;
  try {
    const result = await sendToGroups(text, base64Image, mimeType);
    res.status(200).send({ status: 'ok', ...result });
  } catch (err: any) {
    console.error('❌ Error sending message:', err);
    res.status(500).send({
      error: 'Error sending message',
      details: err instanceof Error ? err.message : String(err),
    });
  }
});

/**
 * Initialize WhatsApp client and start Express server.
 * The bot will automatically reconnect using saved credentials from LocalAuth.
 */
const PORT = process.env.PORT || 4000;
client.initialize();
app.listen(PORT, () => console.log(`🚀 Server running on port ${PORT}`));
