/* ============================================================
 * config.js — 云端同步配置（留空占位，由使用者填写）
 * 全局对象：AppConfig
 * ============================================================
 * 启用云同步需要两步：
 *   1. 在 Supabase 跑 supabase/schema.sql 建表
 *   2. 把下面两个常量填上你的 Project URL 和 anon public key
 *      （Project Settings → API 获取）
 *
 * 若两个都为空字符串，应用自动降级为「纯本地」模式（localStorage），
 * 功能完全不受影响，只是没有跨设备同步。
 * ========================================================== */
(function (global) {
  'use strict';

  var AppConfig = {
    // 例：'https://abcdefghijklmno.supabase.co'
    SUPABASE_URL: '',

    // 例：'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'（anon public key，可公开）
    SUPABASE_ANON_KEY: '',

    /** 是否已配置云端（两个值都非空才视为启用） */
    cloudEnabled: function () {
      return !!(this.SUPABASE_URL && this.SUPABASE_ANON_KEY);
    }
  };

  global.AppConfig = AppConfig;
})(window);
