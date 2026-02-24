import './CopyToClipboard.css';

async function writeClipboardText(clipboardCtx) {
  try {
    await navigator.clipboard.writeText(clipboardCtx.value);
    clipboardCtx.el.classList.add('copy-success');
  } catch (error) {
    console.error('writeClipboardText', error.message);
    clipboardCtx.el.classList.add('copy-error');
  }
  setTimeout(() => {
    clipboardCtx.el.classList.remove('copy-success');
    clipboardCtx.el.classList.remove('copy-error');
  }, 2000);
}

class Registry {
  static dictionary = {};
  static idx = 0;
  new(obj) {
    let newKey = `${(new Date()).getTime()}-${Registry.idx++}`;
    Registry.dictionary[newKey] = obj;
    return newKey;
  }
  update(regKey, updates) {
    Object.assign(Registry.dictionary[regKey], updates);
  }
  delete(regKey) {
    let ctx = Registry.dictionary[regKey];
    delete Registry.dictionary[regKey];
    return ctx;
  }
}

const registry = new Registry();

export default {
  mounted(el, binding, vnode) {
    el.classList.add('clipboard-able');

    let CopyToClipboardCtx = {
      el: el,
      value: binding.value,
      callback: null,
    };

    CopyToClipboardCtx.callback = writeClipboardText.bind(null, CopyToClipboardCtx);

    el.addEventListener('click', CopyToClipboardCtx.callback);

    el.dataset.CopyToClipboardRegistryKey = registry.new(CopyToClipboardCtx);


  },
  updated(el, binding, vnode, prevVnode) {
    registry.update(el.dataset.CopyToClipboardRegistryKey, {
      value: binding.value,
    })
  },
  unmounted(el, binding, vnode) {
    let oldCtx = registry.delete(el.dataset.CopyToClipboardRegistryKey);
    el.removeEventListener('click', oldCtx.callback);
  },
}
