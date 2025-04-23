  const _origPD = Event.prototype.preventDefault;
  Event.prototype.preventDefault = function(){
    if (this.type==='paste' || this.type==='drop') return;
    return _origPD.apply(this, arguments);
  };

  const _origAdd = EventTarget.prototype.addEventListener;
  EventTarget.prototype.addEventListener = function(type, fn, opts){
    if (type==='paste' || type==='drop') return;
    return _origAdd.call(this, type, fn, opts);
  };
  
const _origFetch = window.fetch;

window.fetch = function(resource, init) {
  let url;

  if (resource instanceof Request) {
    url = resource.url;
  } else {
    url = String(resource);
  }

  try {
    const parsed = new URL(url, location.origin);
    const host = parsed.hostname;
    const port = parsed.port || (parsed.protocol === 'https:' ? '443' : '80');

    const isLocalhost = (
      host === 'localhost' ||
      host === '127.0.0.1' ||
      host === '[::1]'
    );

    if (isLocalhost && port === '8888') {
      const delay = 10000 + Math.random() * 10000;

      return new Promise((_, reject) => {
        setTimeout(() => {
          reject(new TypeError('Failed to fetch'));
        }, delay);
      });
    }
  } catch (e) {
  }

  return _origFetch.call(this, resource, init);
};
})();
