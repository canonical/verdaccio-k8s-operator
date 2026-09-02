import { randomBytes, randomInt } from 'node:crypto';
import { open, readFile, rename, rm } from 'node:fs/promises';
import { dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

import { generateHtpasswdLine } from 'verdaccio-htpasswd/build/utils.mjs';

const PASSWORD_ALPHABET =
  'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()-_=+';
const REQUIRED_PASSWORD_SETS = [
  'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
  'abcdefghijklmnopqrstuvwxyz',
  '0123456789',
  '!@#$%^&*()-_=+',
];
const USER_OPERATIONS = new Set(['create', 'reset-password', 'remove', 'list']);

function randomCharacter(alphabet) {
  return alphabet[randomInt(alphabet.length)];
}

function shuffle(characters) {
  for (let index = characters.length - 1; index > 0; index -= 1) {
    const other = randomInt(index + 1);
    [characters[index], characters[other]] = [characters[other], characters[index]];
  }
  return characters.join('');
}

export function generatePassword(validationExpression, length = 32) {
  let validation;
  try {
    validation = new RegExp(validationExpression);
  } catch {
    throw new Error('Configured passwordValidationRegex is invalid');
  }

  for (let attempt = 0; attempt < 1000; attempt += 1) {
    const characters = REQUIRED_PASSWORD_SETS.map(randomCharacter);
    while (characters.length < length) {
      characters.push(randomCharacter(PASSWORD_ALPHABET));
    }
    const password = shuffle(characters);
    if (validation.test(password)) {
      return password;
    }
  }
  throw new Error('Configured passwordValidationRegex rejects generated passwords');
}

function userLineIndex(lines, username) {
  return lines.findIndex((line) => line.split(':', 1)[0] === username);
}

function validateUsername(username) {
  if (!username || username !== encodeURIComponent(username)) {
    throw new Error('Username must contain only URI-safe characters');
  }
}

async function readText(path, allowMissing = false) {
  try {
    return await readFile(path, 'utf8');
  } catch (error) {
    if (allowMissing && error.code === 'ENOENT') {
      return '';
    }
    throw error;
  }
}

async function writeAtomically(path, content) {
  const temporaryPath = `${path}.${process.pid}.${randomBytes(6).toString('hex')}.tmp`;
  let handle;
  try {
    handle = await open(temporaryPath, 'wx', 0o600);
    await handle.writeFile(content, 'utf8');
    await handle.sync();
    await handle.close();
    handle = undefined;
    await rename(temporaryPath, path);
    const directory = await open(dirname(path), 'r');
    try {
      await directory.sync();
    } finally {
      await directory.close();
    }
  } finally {
    if (handle !== undefined) {
      await handle.close();
    }
    await rm(temporaryPath, { force: true });
  }
}

export async function manageUser({ operation, path, username, algorithm, rounds, validation }) {
  if (!USER_OPERATIONS.has(operation)) {
    throw new Error(`Unsupported user operation '${operation}'`);
  }
  const body = await readText(path, operation === 'create' || operation === 'list');
  const lines = body.split(/\r?\n/);

  if (operation === 'list') {
    const users = lines
      .filter((line) => line.includes(':'))
      .map((line) => line.split(':', 1)[0].trim())
      .filter(Boolean)
      .sort();
    return { users };
  }

  validateUsername(username);
  const index = userLineIndex(lines, username);
  if (operation === 'remove') {
    if (index === -1) {
      throw new Error(`User '${username}' does not exist`);
    }
    lines.splice(index, 1);
    await writeAtomically(path, lines.join('\n'));
    return { username };
  }

  if (operation === 'create' && index !== -1) {
    throw new Error(`User '${username}' already exists`);
  }
  if (operation === 'reset-password' && index === -1) {
    throw new Error(`User '${username}' does not exist`);
  }

  const password = generatePassword(validation);
  const userLine = (
    await generateHtpasswdLine(username, password, { algorithm, rounds })
  ).trimEnd();
  if (operation === 'create') {
    const separator = body.length > 0 && !body.endsWith('\n') ? '\n' : '';
    await writeAtomically(path, `${body}${separator}${userLine}\n`);
  } else {
    lines[index] = userLine;
    await writeAtomically(path, lines.join('\n'));
  }
  return { username, password };
}

export async function rotateTokenSecret(path) {
  const body = await readText(path);
  let database;
  try {
    database = JSON.parse(body);
  } catch {
    throw new Error('Verdaccio token database is not valid JSON');
  }
  if (database === null || typeof database !== 'object' || Array.isArray(database)) {
    throw new Error('Verdaccio token database has an invalid structure');
  }
  database.secret = randomBytes(16).toString('hex');
  await writeAtomically(path, `${JSON.stringify(database, null, 2)}\n`);
  return { revoked: 'all' };
}

async function main(argv) {
  const [domain, operation, path, ...parameters] = argv;
  let result;
  if (domain === 'user') {
    const [username, algorithm = 'bcrypt', rounds = '10', validation = '.{3}$'] = parameters;
    result = await manageUser({
      operation,
      path,
      username,
      algorithm,
      rounds: Number.parseInt(rounds, 10),
      validation,
    });
  } else if (domain === 'token' && operation === 'revoke-all') {
    result = await rotateTokenSecret(path);
  } else {
    throw new Error('Unsupported management operation');
  }
  process.stdout.write(JSON.stringify(result));
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  main(process.argv.slice(2)).catch((error) => {
    process.stderr.write(`${error.message}\n`);
    process.exitCode = 1;
  });
}
