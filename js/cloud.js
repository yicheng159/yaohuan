/* ============================================================
 * cloud.js — 云端同步封装（Supabase）
 * 全局对象：Cloud
 *   init()            -> Promise<boolean>  初始化（加载SDK、连接）
 *   enabled()         -> boolean           是否已配置并连接
 *   loadAll()         -> Promise<[tpl]>    拉取全部云端模板
 *   save(tpl)         -> Promise<void>      upsert 单个模板
 *   remove(id)        -> Promise<void>      删除
 *   subscribe(cb)     -> 订阅变更（实时），cb(list) 收到新全量
 *   status            -> 'local'|'connecting'|'online'|'offline'
 * 设计：云端为主、localStorage 为缓存；断网自动降级本地。
 * ========================================================== */
(function (global) {
  'use strict';

  var SB = null;            // supabase client
  var status = 'local';     // 初始为纯本地
  var channel = null;

  // Supabase JS SDK CDN（带本地 lib 兜底）
  var SDK_CDN = 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2';
  var SDK_LOCAL = 'lib/supabase-js.min.js';

  function loadScript(src) {
    return new Promise(function (resolve, reject) {
      var s = document.createElement('script');
      s.src = src;
      s.onload = function () { resolve(); };
      s.onerror = function () { reject(new Error('脚本加载失败: ' + src)); };
      document.head.appendChild(s);
    });
  }

  function init() {
    if (!global.AppConfig || !global.AppConfig.cloudEnabled()) {
      status = 'local';
      return Promise.resolve(false);
    }
    if (SB) return Promise.resolve(true);

    status = 'connecting';
    var loader = (typeof global.supabase !== 'undefined')
      ? Promise.resolve()
      : loadScript(SDK_CDN).catch(function () { return loadScript(SDK_LOCAL); });

    return loader.then(function () {
      if (typeof global.supabase === 'undefined' || !global.supabase.createClient) {
        throw new Error('Supabase SDK 未加载');
      }
      SB = global.supabase.createClient(
        global.AppConfig.SUPABASE_URL,
        global.AppConfig.SUPABASE_ANON_KEY
      );
      status = 'online';
      return true;
    }).catch(function (e) {
      console.warn('云端初始化失败，降级本地：', e && e.message);
      status = 'offline';
      return false;
    });
  }

  function enabled() { return !!SB && status === 'online'; }

  function rowToTpl(r) {
    return {
      id: r.id,
      name: r.name,
      description: r.description || '',
      settings: typeof r.settings === 'string' ? JSON.parse(r.settings) : (r.settings || {}),
      fields: typeof r.fields === 'string' ? JSON.parse(r.fields) : (r.fields || []),
      content: r.content || '',
      updatedAt: r.updated_at || 0,
      createdAt: r.created_at || 0
    };
  }

  function loadAll() {
    if (!enabled()) return Promise.resolve(null); // null = 不可用，走本地
    return SB.from('templates').select('*').then(function (res) {
      if (res.error) throw res.error;
      return (res.data || []).map(rowToTpl);
    });
  }

  function save(tpl) {
    if (!enabled()) return Promise.resolve(false);
    var row = {
      id: tpl.id,
      name: tpl.name,
      description: tpl.description || '',
      settings: JSON.stringify(tpl.settings || {}),
      fields: JSON.stringify(tpl.fields || []),
      content: tpl.content || '',
      updated_at: tpl.updatedAt || Date.now(),
      created_at: tpl.createdAt || tpl.updatedAt || Date.now()
    };
    return SB.from('templates').upsert(row).then(function (res) {
      if (res.error) throw res.error;
      return true;
    });
  }

  function remove(id) {
    if (!enabled()) return Promise.resolve(false);
    return SB.from('templates').delete().eq('id', id).then(function (res) {
      if (res.error) throw res.error;
      return true;
    });
  }

  function subscribe(cb) {
    if (!enabled()) return;
    try {
      channel = SB.channel('templates-changes')
        .on('postgres_changes', { event: '*', schema: 'public', table: 'templates' }, function () {
          loadAll().then(function (list) { if (list && cb) cb(list); }).catch(function () {});
        })
        .subscribe();
    } catch (e) { /* 订阅失败不影响主流程 */ }
  }

  global.Cloud = {
    init: init,
    enabled: enabled,
    loadAll: loadAll,
    save: save,
    remove: remove,
    subscribe: subscribe,
    get status() { return status; }
  };
})(window);
