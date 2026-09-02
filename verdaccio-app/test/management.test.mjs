import assert from 'node:assert/strict';
import { mkdtemp, readFile, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { test } from 'node:test';

import { verifyPassword } from 'verdaccio-htpasswd/build/utils.mjs';

import { manageUser, rotateTokenSecret } from '../management.mjs';

async function userOperation(path, operation, username, algorithm = 'bcrypt') {
  return manageUser({
    operation,
    path,
    username,
    algorithm,
    rounds: 4,
    validation: '.{12}$',
  });
}

for (const algorithm of ['bcrypt', 'md5', 'sha1', 'crypt']) {
  test(`creates and resets ${algorithm} users`, async () => {
    const directory = await mkdtemp(join(tmpdir(), 'verdaccio-management-'));
    const path = join(directory, 'htpasswd');

    const admin = await userOperation(path, 'create', 'admin', algorithm);
    const user = await userOperation(path, 'create', 'alice', algorithm);
    const listed = await userOperation(path, 'list');

    assert.deepEqual(listed.users, ['admin', 'alice']);
    assert.notEqual(admin.password, user.password);
    const before = await readFile(path, 'utf8');
    const oldHash = before.split('\n').find((line) => line.startsWith('alice:')).split(':')[1];
    assert.equal(await verifyPassword(user.password, oldHash), true);

    const reset = await userOperation(path, 'reset-password', 'alice', algorithm);
    const after = await readFile(path, 'utf8');
    const newHash = after.split('\n').find((line) => line.startsWith('alice:')).split(':')[1];
    assert.equal(await verifyPassword(user.password, newHash), false);
    assert.equal(await verifyPassword(reset.password, newHash), true);

    await userOperation(path, 'remove', 'alice', algorithm);
    assert.deepEqual((await userOperation(path, 'list')).users, ['admin']);
  });
}

test('rejects duplicate and missing users without changing the file', async () => {
  const directory = await mkdtemp(join(tmpdir(), 'verdaccio-management-'));
  const path = join(directory, 'htpasswd');
  await userOperation(path, 'create', 'alice');
  const original = await readFile(path, 'utf8');

  await assert.rejects(userOperation(path, 'create', 'alice'), /already exists/);
  await assert.rejects(userOperation(path, 'reset-password', 'missing'), /does not exist/);
  await assert.rejects(userOperation(path, 'remove', 'missing'), /does not exist/);
  assert.equal(await readFile(path, 'utf8'), original);
});

test('rejects unsafe usernames without changing the file', async () => {
  const directory = await mkdtemp(join(tmpdir(), 'verdaccio-management-'));
  const path = join(directory, 'htpasswd');
  await userOperation(path, 'create', 'alice');
  const original = await readFile(path, 'utf8');

  for (const username of ['alice:$2b$fake', 'alice\nbob']) {
    await assert.rejects(userOperation(path, 'create', username), /URI-safe characters/);
  }
  assert.equal(await readFile(path, 'utf8'), original);
});

test('rejects unsupported user operations without changing the file', async () => {
  const directory = await mkdtemp(join(tmpdir(), 'verdaccio-management-'));
  const path = join(directory, 'htpasswd');
  await userOperation(path, 'create', 'alice');
  const original = await readFile(path, 'utf8');

  await assert.rejects(userOperation(path, 'rename', 'alice'), /Unsupported user operation/);
  assert.equal(await readFile(path, 'utf8'), original);
});

test('rotates only the token signing secret', async () => {
  const directory = await mkdtemp(join(tmpdir(), 'verdaccio-management-'));
  const path = join(directory, '.verdaccio-db.json');
  await writeFile(path, JSON.stringify({ list: ['private-package'], secret: 'a'.repeat(32) }));

  assert.deepEqual(await rotateTokenSecret(path), { revoked: 'all' });
  const database = JSON.parse(await readFile(path, 'utf8'));

  assert.deepEqual(database.list, ['private-package']);
  assert.match(database.secret, /^[0-9a-f]{32}$/);
  assert.notEqual(database.secret, 'a'.repeat(32));
});
