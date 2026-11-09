"""Caller-owned transactions. No engine, commit, rollback, DDL or network calls."""
import hashlib
import json


class RevisionConflict(Exception):
    pass


def context_key(context):
    fields = {'recipe_id', 'recipe_version', 'servings', 'ingredient_id',
              'requirement_raw', 'evidence_raw'}
    if not isinstance(context, dict) or set(context) != fields:
        raise ValueError('Complete recipe context is required')
    if any(not isinstance(v, str) or not v.strip() for v in context.values()):
        raise ValueError('Nonempty context values are required')
    encoded = json.dumps(context, sort_keys=True, ensure_ascii=False).encode('utf-8')
    return hashlib.sha256(encoded).hexdigest()


class RecipeSessionStore:
    def __init__(self, conn, statement_factory=None):
        # Production uses sqlalchemy.text. Offline tests explicitly use str.
        if statement_factory is None:
            from sqlalchemy import text
            statement_factory = text
        self.conn = conn
        self.statement = statement_factory

    def _identity(self, session_id, ingredient_id):
        if any(not isinstance(v, str) or not v.strip() for v in (session_id, ingredient_id)):
            raise ValueError('Session and ingredient identity are required')
        return dict(session_id=session_id, ingredient_id=ingredient_id)

    def load(self, session_id, ingredient_id):
        params = self._identity(session_id, ingredient_id)
        row = self.conn.execute(self.statement('''
            SELECT context_key, state_json, revision
            FROM recipe_followup_state
            WHERE session_id=:session_id AND ingredient_id=:ingredient_id
        '''), params).mappings().first()
        if row is None:
            return None
        state = json.loads(row['state_json'])
        if state['session_id'] != session_id or state['context']['ingredient_id'] != ingredient_id:
            raise ValueError('Stored state identity mismatch')
        if context_key(state['context']) != row['context_key']:
            raise ValueError('Stored context mismatch')
        return dict(state=state, revision=row['revision'])

    def save(self, session_id, context, state, expected_revision):
        params = self._identity(session_id, context.get('ingredient_id'))
        key = context_key(context)
        if state.get('session_id') != session_id or state.get('context') != context:
            raise ValueError('State identity mismatch')
        if type(expected_revision) is not int or expected_revision < 0:
            raise ValueError('Revision must be a nonnegative integer')
        params.update(context_key=key, state_json=json.dumps(state, ensure_ascii=False,
                       allow_nan=False), expected_revision=expected_revision)
        if expected_revision == 0:
            sql = '''INSERT INTO recipe_followup_state
                     (session_id, ingredient_id, context_key, state_json, revision)
                     VALUES (:session_id, :ingredient_id, :context_key, :state_json, 1)
                     ON CONFLICT (session_id, ingredient_id) DO NOTHING'''
        else:
            sql = '''UPDATE recipe_followup_state
                     SET context_key=:context_key, state_json=:state_json,
                         revision=revision+1, updated_at=CURRENT_TIMESTAMP
                     WHERE session_id=:session_id AND ingredient_id=:ingredient_id
                       AND revision=:expected_revision'''
        result = self.conn.execute(self.statement(sql), params)
        if result.rowcount != 1:
            raise RevisionConflict('State changed; reload before retrying')
        return expected_revision + 1

    def load_matching(self, session_id, context):
        record = self.load(session_id, context['ingredient_id'])
        if record is None or record['state']['context'] != context:
            return None
        return record
