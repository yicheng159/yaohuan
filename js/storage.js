/* ============================================================
 * storage.js — 混合存储层（云端为主 + localStorage 缓存）
 * 全局对象：Store
 *   - 离线/未配置云端：行为与旧版完全一致（localStorage）
 *   - 已配置云端：以云端为准；启动时拉云端覆盖本地；保存先写本地再异步推云端
 * 依赖：Cloud（js/cloud.js）
 * ========================================================== */
(function (global) {
  'use strict';

  var KEY = 'ppt_templates_v1';

  function _read() {
    try {
      var raw = localStorage.getItem(KEY);
      var data = raw ? JSON.parse(raw) : [];
      return Array.isArray(data) ? data : [];
    } catch (e) {
      console.warn('读取模板失败，已重置为空列表', e);
      return [];
    }
  }

  function _write(list) {
    localStorage.setItem(KEY, JSON.stringify(list));
  }

  /** 用云端列表覆盖本地（云端优先） */
  function _overwriteWithCloud(list) {
    if (!Array.isArray(list)) return;
    _write(list);
  }

  /** 把本地全部推到云端（用于首次配置云端后的迁移） */
  function pushLocalToCloud() {
    if (!global.Cloud || !global.Cloud.enabled()) return Promise.resolve(false);
    var list = _read();
    var chain = Promise.resolve();
    list.forEach(function (t) { chain = chain.then(function () { return global.Cloud.save(t); }); });
    return chain.then(function () { return true; });
  }

  var Store = {
    /** 启动同步：若云端可用，拉取并覆盖本地；否则保持本地 */
    syncFromCloud: function () {
      if (!global.Cloud || !global.Cloud.enabled()) return Promise.resolve(false);
      return global.Cloud.loadAll().then(function (list) {
        if (list === null) return false;     // 云端不可用
        _overwriteWithCloud(list);
        return true;
      }).catch(function () { return false; });
    },

    /** 返回全部模板（按更新时间倒序） */
    all: function () {
      return _read().sort(function (a, b) {
        return (b.updatedAt || 0) - (a.updatedAt || 0);
      });
    },

    /** 按 id 获取单个模板 */
    get: function (id) {
      return _read().filter(function (t) { return t.id === id; })[0] || null;
    },

    /** 新增或更新模板，返回保存后的对象（并异步推云端） */
    upsert: function (tpl) {
      var list = _read();
      tpl.updatedAt = Date.now();
      if (!tpl.id) {
        tpl.id = 'tpl_' + Date.now().toString(36) + Math.random().toString(36).slice(2, 7);
        tpl.createdAt = tpl.updatedAt;
        list.push(tpl);
      } else {
        var idx = -1;
        list.forEach(function (t, i) { if (t.id === tpl.id) idx = i; });
        if (idx >= 0) list[idx] = tpl; else list.push(tpl);
      }
      _write(list);
      // 异步推云端（不阻塞 UI）
      if (global.Cloud && global.Cloud.enabled()) {
        global.Cloud.save(tpl).catch(function (e) { console.warn('云端保存失败：', e && e.message); });
      }
      return tpl;
    },

    /** 删除模板（并异步推云端） */
    remove: function (id) {
      _write(_read().filter(function (t) { return t.id !== id; }));
      if (global.Cloud && global.Cloud.enabled()) {
        global.Cloud.remove(id).catch(function (e) { console.warn('云端删除失败：', e && e.message); });
      }
    },

    /** 首次配置云端后，是否曾做过本地→云端迁移（防重复） */
    _pushLocalToCloud: pushLocalToCloud
  };

  global.Store = Store;
})(window);
