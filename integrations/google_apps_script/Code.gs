/**
 * KEIBA NINE - private JRDB mail summarizer (standalone Google Apps Script).
 *
 * Runs INSIDE the owner's Google account. No paid email text, provider metrics,
 * odds, credentials, rankings or raw mail is sent to Render. It stores only
 * venue/race/start, the email's timestamp, going and three paddock horse numbers.
 *
 * Requires a one-time Gmail authorization + Web app deployment by the owner.
 * Never publish KEIBA_BRIDGE_TOKEN, the deployment URL/token pair, or mail.
 */
'use strict';
const KEIBA_TZ = 'Asia/Tokyo';
const KEIBA_SCHEMA = 'keiba-nine-mail-bridge-v1';
const KEIBA_VENUES = ['東京', '京都', '福島'];
const KEIBA_ALLOWED = [
  'jrdb-minig2@mailman.jrdb.com',
  'jrdb-hotg3@mailman.jrdb.com'
];
function keibaDate_(date) {
  return Utilities.formatDate(date, KEIBA_TZ, 'yyyy-MM-dd');
}
function keibaClock_(date) {
  return Utilities.formatDate(date, KEIBA_TZ, 'HH:mm');
}
function keibaMinutes_(hhmm) {
  const nums = String(hhmm).split(':').map(Number);
  return nums[0] * 60 + nums[1];
}
function keibaMatchEmail_(message) {
  const subject = String(message.getSubject() || '');
  const match = subject.match(/^\[Jrdb-(minig2|hotg3)\s+\d+\]\s+(?:\d+回)?(東京|京都|福島)\d+日([1-9]|1[0-2])R$/i);
  if (!match) return null;
  const expectedSender = 'jrdb-' + match[1].toLowerCase() + '@mailman.jrdb.com';
  const actualSender = String(message.getFrom() || '').toLowerCase();
  if (!actualSender.includes(expectedSender)) return null;
  const receivedAt = message.getDate();
  const data = String(message.getPlainBody() || '');
  const clock = data.match(/([01]?\d|2[0-3]):([0-5]\d)\s*発走/);
  if (!clock) return null;
  const time = clock[1].padStart(2, '0') + ':' + clock[2];
  const observedAt = keibaClock_(receivedAt);
  if (keibaMinutes_(observedAt) > keibaMinutes_(time) - 2) return null;
  const entry = {
    track: match[2], race: Number(match[3]),
    time: time, observedAt: observedAt,
    type: match[1].toLowerCase(), date: keibaDate_(receivedAt),
    going: '未確認', paddock: []
  };
  if (entry.type === 'hotg3') {
    const going = data.match(/馬場[：:]\s*(良|稍重|重|不良)/);
    if (going) entry.going = going[1];
  } else {
    // The mini mail has an explicit "総合 パドック点" header.
    // Read only the top three paddock horse *numbers*, never the scores.
    const section = data.split(/総合\s+パドック点/)[1];
    if (section) {
      const top = section.split(/パドック☆|激走[：:]/)[0];
      for (const line of top.split(/\r?\n/)) {
        const m = line.match(/^\s*[◎○▲注△☆]\s*\d{1,2}\s+[◎○▲注△☆]\s*(\d{1,2})(?:\s|\()/);
        if (m) {
          const number = Number(m[1]);
          if (number >= 1 && number <= 18 && !entry.paddock.includes(number))
            entry.paddock.push(number);
        }
        if (entry.paddock.length === 3) break;
      }
    }
  }
  return entry;
}
/**
 * Install once from the Apps Script editor. The trigger is idempotent.
 * A minute is a polling interval, NOT guaranteed exact delivery timing.
 */
function installKeibaMailTrigger() {
  const properties = PropertiesService.getScriptProperties();
  if (!properties.getProperty('KEIBA_BRIDGE_TOKEN'))
    throw new Error('First run createKeibaBridgeToken and save the value privately.');
  const found = ScriptApp.getProjectTriggers().some(trigger =>
    trigger.getHandlerFunction() === 'syncKeibaMail');
  if (!found)
    ScriptApp.newTrigger('syncKeibaMail').timeBased().everyMinutes(1).create();
}
function createKeibaBridgeToken() {
  const properties = PropertiesService.getScriptProperties();
  if (!properties.getProperty('KEIBA_BRIDGE_TOKEN')) {
    const token = (Utilities.getUuid() + Utilities.getUuid()).replace(/-/g, '');
    properties.setProperty('KEIBA_BRIDGE_TOKEN', token);
  }
  // Read and copy KEIBA_BRIDGE_TOKEN from Project Settings -> Script properties.
  // Deliberately do not print a secret in execution logs.
}
/** Polls the owner's own inbox. Never changes any forecast or purchase. */
function syncKeibaMail() {
  const now = new Date();
  const today = keibaDate_(now);
  const hhmm = keibaClock_(now);
  if (keibaMinutes_(hhmm) < 9 * 60 || keibaMinutes_(hhmm) >= 17 * 60)
    return;
  const lock = LockService.getScriptLock();
  if (!lock.tryLock(1000)) return;
  try {
    const properties = PropertiesService.getScriptProperties();
    const key = 'KEIBA_MAIL_DAY_' + today.replace(/-/g, '');
    const existing = JSON.parse(properties.getProperty(key) || '{}');
    const records = existing.records || {};
    const processed = new Set(existing.processed || []);
    for (const sender of KEIBA_ALLOWED) {
      const query = 'from:' + sender + ' newer_than:3h';
      const threads = GmailApp.search(query, 0, 60);
      for (const thread of threads) {
        for (const message of thread.getMessages()) {
          const messageId = message.getId();
          if (processed.has(messageId)) continue;
          processed.add(messageId);
          const parsed = keibaMatchEmail_(message);
          if (!parsed || parsed.date !== today) continue;
          // Even if the email was received pre-start, a delayed trigger must
          // NEVER newly publish a record at or after the race's cutoff.
          if (keibaMinutes_(hhmm) >= keibaMinutes_(parsed.time) - 2)
            continue;
          const id = parsed.track + ':' + parsed.race;
          const entry = records[id] || {
            track: parsed.track, race: parsed.race, time: parsed.time,
            observedAt: parsed.observedAt, ground: '未確認', paddock: []
          };
          if (entry.time !== parsed.time) continue;
          if (entry.observedAt < parsed.observedAt)
            entry.observedAt = parsed.observedAt;
          if (parsed.going !== '未確認') entry.ground = parsed.going;
          if (parsed.paddock.length) entry.paddock = parsed.paddock;
          records[id] = entry;
        }
      }
    }
    const values = Object.keys(records).map(k => records[k]);
    // Hold the going-only part privately until a mini paddock mail arrives.
    // Incomplete records are NEVER returned from doPost.
    // Keep only minimal records, not the mailbox contents. Max ScriptProperty 9KB.
    const saved = {records: {}, processed: Array.from(processed).slice(-180)};
    for (const v of values) saved.records[v.track + ':' + v.race] = v;
    properties.setProperty(key, JSON.stringify(saved));
    properties.setProperty('KEIBA_MAIL_LAST_CHECK', today + ' ' + hhmm);
    // Remove the previous day's ephemeral notes; never keep source texts.
    const old = new Date(now.getTime() - 86400000);
    properties.deleteProperty('KEIBA_MAIL_DAY_' + keibaDate_(old).replace(/-/g, ''));
  } finally {
    lock.releaseLock();
  }
}
function keibaSecureCompare_(actual, expected) {
  if (typeof actual !== 'string' || typeof expected !== 'string') return false;
  let mismatch = actual.length ^ expected.length;
  for (let i = 0; i < Math.max(actual.length, expected.length); i++)
    mismatch |= (actual.charCodeAt(i) || 0) ^ (expected.charCodeAt(i) || 0);
  return mismatch === 0;
}
/** Private POST reader for the authenticated Render backend. */
function doPost(e) {
  let outgoing = {ok: false};
  // Private execution-log labels only; never log secrets, mail, or request data.
  let check = 'request_invalid';
  try {
    if (!e || !e.postData || String(e.postData.contents || '').length > 1000)
      throw new Error('Bad request');
    const body = JSON.parse(e.postData.contents);
    const properties = PropertiesService.getScriptProperties();
    const token = properties.getProperty('KEIBA_BRIDGE_TOKEN');
    check = 'secret_missing';
    if (!token || token.length < 32) throw new Error('Unauthorized');
    check = 'token_mismatch';
    if (!keibaSecureCompare_(body.token, token)) throw new Error('Unauthorized');
    check = 'action_invalid';
    if (body.action !== 'read') throw new Error('Unauthorized');
    check = 'date_invalid';
    if (!/^\d{4}-\d{2}-\d{2}$/.test(body.date)) throw new Error('Unauthorized');
    check = 'date_mismatch';
    if (body.date !== keibaDate_(new Date())) throw new Error('Unauthorized');
    check = 'stored_notes_invalid';
    const key = 'KEIBA_MAIL_DAY_' + body.date.replace(/-/g, '');
    const store = JSON.parse(properties.getProperty(key) || '{}');
    const races = Object.values(store.records || {}).filter(r =>
      KEIBA_VENUES.includes(r.track) && Number.isInteger(r.race) &&
      r.race >= 1 && r.race <= 12 &&
      /^\d\d:\d\d$/.test(r.time) && /^\d\d:\d\d$/.test(r.observedAt) &&
      keibaMinutes_(r.observedAt) < keibaMinutes_(r.time) - 1 &&
      ['良', '稍重', '重', '不良', '未確認'].includes(r.ground) &&
      Array.isArray(r.paddock) && r.paddock.length >= 1 &&
      r.paddock.length <= 5 &&
      r.paddock.every(n => Number.isInteger(n) && n > 0 && n <= 18)
    ).slice(0, 36);
    outgoing = {schema: KEIBA_SCHEMA, date: body.date, races: races};
  } catch (_) {
    // Coarse private log only. Never echo auth inputs or source material.
    console.warn('KEIBA_BRIDGE_CHECK=' + check);
  }
  return ContentService.createTextOutput(JSON.stringify(outgoing))
    .setMimeType(ContentService.MimeType.JSON);
}
