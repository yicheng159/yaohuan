/* ============================================================
 * fields.js — 字段类型与占位符工具
 * 全局对象：Fields
 * 占位符语法：{{ 字段key }}  （key 支持字母/数字/下划线/中文）
 * ========================================================== */
(function (global) {
  'use strict';

  // 字段类型定义
  var TYPES = {
    text:   { label: '文本',   hint: '单行或段落文本' },
    number: { label: '数值',   hint: '数字，可带单位/小数位' },
    date:   { label: '日期',   hint: '日历日期' },
    table:  { label: '表格',   hint: '上传 Excel 作为数据源，渲染为表格' },
    select: { label: '下拉',   hint: '从预设选项中选择' }
  };

  // 匹配 {{ key }}
  var TOKEN_RE = /\{\{\s*([A-Za-z0-9_一-龥]+)\s*\}\}/g;

  /** 从 HTML 中提取所有占位符 key（去重，保序） */
  function extractTokens(html) {
    if (!html) return [];
    var found = [];
    var seen = {};
    var m;
    TOKEN_RE.lastIndex = 0;
    while ((m = TOKEN_RE.exec(html)) !== null) {
      var k = m[1];
      if (!seen[k]) { seen[k] = true; found.push(k); }
    }
    return found;
  }

  /** 校验并规范化 key（仅保留字母数字下划线中文，首字符非数字） */
  function normalizeKey(raw) {
    var s = (raw || '').toString().trim().replace(/\s+/g, '_');
    s = s.replace(/[^\w一-龥]/g, ''); // 移除非允许字符
    if (!s) s = 'field';
    if (/^[0-9]/.test(s)) s = 'f_' + s;
    return s;
  }

  /** HTML 转义，防止注入与标签破坏 */
  function esc(s) {
    if (s === null || s === undefined) return '';
    return String(s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  global.Fields = {
    TYPES: TYPES,
    extractTokens: extractTokens,
    normalizeKey: normalizeKey,
    esc: esc,
    TOKEN_RE: TOKEN_RE
  };
})(window);
