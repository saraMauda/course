/* Runs Python (Pyodide) off the main thread so the page stays responsive. Classic worker: importScripts. */
const PYODIDE_URL = 'https://cdn.jsdelivr.net/pyodide/v0.29.5/full/';
importScripts(PYODIDE_URL + 'pyodide.js');

const COHERE_SHIM = `
import json
from js import XMLHttpRequest

API = "https://api.cohere.com/v2"


class ApiError(Exception):
    def __init__(self, status_code, body):
        self.status_code = status_code
        self.body = body
        super().__init__(f"status_code: {status_code}, body: {body}")


class _Obj:
    def __init__(self, d):
        for k, v in d.items():
            setattr(self, k, _wrap(v))
        if "float" in d:
            self.float_ = self.float

    def __repr__(self):
        return "Obj(" + ", ".join(self.__dict__) + ")"


def _wrap(v):
    if isinstance(v, dict):
        return _Obj(v)
    if isinstance(v, list):
        return [_wrap(x) for x in v]
    return v


class ClientV2:
    def __init__(self, api_key=None, **kwargs):
        if not api_key:
            raise ValueError("api_key is required")
        self._key = str(api_key).strip()

    def _post(self, path, body):
        body = {k: v for k, v in body.items() if v is not None}
        xhr = XMLHttpRequest.new()
        xhr.open("POST", API + path, False)  # synchronous: allowed inside a worker
        xhr.setRequestHeader("Authorization", "Bearer " + self._key)
        xhr.setRequestHeader("Content-Type", "application/json")
        try:
            xhr.send(json.dumps(body))
        except Exception as e:
            raise ApiError(0, "network error: " + str(e))
        if xhr.status < 200 or xhr.status >= 300:
            raise ApiError(xhr.status, xhr.responseText)
        return _wrap(json.loads(xhr.responseText))

    def embed(self, texts, model, input_type, embedding_types=None, **kwargs):
        return self._post("/embed", dict(texts=texts, model=model, input_type=input_type,
                                         embedding_types=embedding_types, **kwargs))

    def chat(self, model, messages, response_format=None, temperature=None, **kwargs):
        return self._post("/chat", dict(model=model, messages=messages, response_format=response_format,
                                        temperature=temperature, **kwargs))
`;

const COLAB_USERDATA_SHIM = `
import js


class SecretNotFoundError(Exception):
    pass


class NotebookAccessError(Exception):
    pass


def get(name):
    secrets = js.secrets.to_py() if js.secrets else {}
    value = secrets.get(name)
    if not value:
        raise SecretNotFoundError(f"המפתח {name} לא הוגדר. מדביקים אותו בשדה 'מפתח Cohere' בראש העמוד.")
    return value
`;

let pyodide = null;
let installed = new Set();
self.secrets = {};

const post = (msg) => self.postMessage(msg);

async function init() {
  post({ type: 'status', text: 'טוען את פייתון (פעם ראשונה לוקח כמה שניות)...' });
  pyodide = await loadPyodide({ indexURL: PYODIDE_URL });
  await pyodide.loadPackage(['numpy', 'micropip']);

  pyodide.FS.mkdirTree('/shims/google/colab');
  pyodide.FS.writeFile('/shims/cohere.py', COHERE_SHIM);
  pyodide.FS.writeFile('/shims/google/__init__.py', '');
  pyodide.FS.writeFile('/shims/google/colab/__init__.py', 'from . import userdata\n');
  pyodide.FS.writeFile('/shims/google/colab/userdata.py', COLAB_USERDATA_SHIM);
  pyodide.runPython("import sys; sys.path.insert(0, '/shims')");

  pyodide.FS.chdir('/home/pyodide');
  post({ type: 'ready' });
}

/** Keeps only the user's own frames of a Pyodide traceback, dropping the interpreter's internal ones. */
function cleanTrace(message) {
  const lines = String(message).split('\n');
  const start = lines.findIndex((l) => l.includes('<exec>'));
  if (start === -1) return lines.slice(-6).join('\n');
  const from = start > 0 && lines[start - 1].startsWith('Traceback') ? start - 1 : start;
  return lines.slice(from).join('\n');
}

async function run({ id, code, packages }) {
  const out = (text) => post({ type: 'stdout', id, text });
  pyodide.setStdout({ batched: out });
  pyodide.setStderr({ batched: out });
  try {
    const fresh = (packages || []).filter((p) => !installed.has(p));
    if (fresh.length) {
      out('מתקין: ' + fresh.join(', '));
      const micropip = pyodide.pyimport('micropip');
      await micropip.install(fresh);
      fresh.forEach((p) => installed.add(p));
    }
    const result = await pyodide.runPythonAsync(code);
    if (result !== undefined && result !== null) out(String(result));
    post({ type: 'done', id });
  } catch (e) {
    post({ type: 'done', id, error: cleanTrace(e && e.message ? e.message : e) });
  }
}

function listFiles() {
  const dir = '/home/pyodide';
  const files = pyodide.FS.readdir(dir)
    .filter((n) => n !== '.' && n !== '..' && !n.startsWith('.'))
    .map((n) => ({ n, st: pyodide.FS.stat(dir + '/' + n) }))
    .filter(({ st }) => pyodide.FS.isFile(st.mode))
    .map(({ n, st }) => ({ name: n, size: st.size }));
  post({ type: 'files', files });
}

self.onmessage = async ({ data }) => {
  try {
    if (data.type === 'init') return await init();
    if (!pyodide) return;
    if (data.type === 'run') return await run(data);
    if (data.type === 'secrets') {
      self.secrets = data.value || {};
      return;
    }
    if (data.type === 'writeFile') {
      pyodide.FS.writeFile('/home/pyodide/' + data.name, new Uint8Array(data.data));
      return listFiles();
    }
    if (data.type === 'readFile') {
      const bytes = pyodide.FS.readFile('/home/pyodide/' + data.name);
      return post({ type: 'file', name: data.name, data: bytes.buffer });
    }
    if (data.type === 'listFiles') return listFiles();
  } catch (e) {
    post({ type: 'fatal', text: String(e && e.message ? e.message : e) });
  }
};
