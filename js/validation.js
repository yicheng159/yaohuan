/* ============================================================
 * validation.js — 字段校验引擎
 * 全局对象：Validation
 * 依赖：无
 * 规则集中在每个字段的 f.validation 上：
 *   text:   { minLen, maxLen, pattern, patternMsg }
 *   number: { min, max, integer }
 *   date:   { min, max }   （格式 yyyy-mm-dd 或可被 Date.parse 解析）
 *   select: （仅必填）
 *   table:  （仅必填：必须至少有 1 行数据）
 * 必填（required）仍为字段顶层属性。
 * ========================================================== */
(function (global) {
  'use strict';

  function toStr(v) {
    if (v === undefined || v === null) return '';
    if (Array.isArray(v)) return ''; // 表格等对象不在此校验
    return String(v);
  }

  /**
   * 校验单个字段值。
   * @param {object} f 字段定义（含 type / required / validation / label / key）
   * @param {any} value 待校验值
   * @returns {string|null} 错误信息，或 null 表示通过
   */
  function validateField(f, value) {
    if (!f) return null;
    var label = f.label || f.key || '字段';
    var raw = toStr(value);
    var v = raw.trim();

    if (f.required && !v) {
      return label + '：必填项不能为空';
    }
    // 非必填且为空 → 其余规则不再校验
    if (!v) return null;

    var r = f.validation || {};
    var type = f.type;

    if (type === 'number') {
      var num = Number(v);
      if (v !== '' && isNaN(num)) return label + '：必须是数字';
      if (r.integer && !Number.isInteger(num)) return label + '：必须为整数';
      if (r.min !== undefined && r.min !== '' && !isNaN(Number(r.min)) && num < Number(r.min))
        return label + '：不能小于 ' + r.min;
      if (r.max !== undefined && r.max !== '' && !isNaN(Number(r.max)) && num > Number(r.max))
        return label + '：不能大于 ' + r.max;
      if (r.min !== undefined && r.min !== '' && isNaN(Number(r.min))) return label + '：最小值配置无效';
      if (r.max !== undefined && r.max !== '' && isNaN(Number(r.max))) return label + '：最大值配置无效';
    } else if (type === 'date') {
      var t = Date.parse(v);
      if (isNaN(t)) return label + '：日期格式不正确（建议 yyyy-mm-dd）';
      if (r.min && !isNaN(Date.parse(r.min)) && t < Date.parse(r.min))
        return label + '：不能早于 ' + r.min;
      if (r.max && !isNaN(Date.parse(r.max)) && t > Date.parse(r.max))
        return label + '：不能晚于 ' + r.max;
    } else if (type === 'text') {
      if (r.minLen !== undefined && r.minLen !== '' && !isNaN(Number(r.minLen)) && v.length < Number(r.minLen))
        return label + '：至少 ' + r.minLen + ' 个字符';
      if (r.maxLen !== undefined && r.maxLen !== '' && !isNaN(Number(r.maxLen)) && v.length > Number(r.maxLen))
        return label + '：最多 ' + r.maxLen + ' 个字符';
      if (r.pattern) {
        try {
          if (!(new RegExp(r.pattern)).test(v))
            return label + '：' + (r.patternMsg ? r.patternMsg : '格式不正确');
        } catch (e) { /* 非法正则忽略 */ }
      }
    } else if (type === 'table') {
      if (f.required) {
        var rows = (value && value.rows) ? value.rows : null;
        if (!rows || !rows.length) return label + '：表格数据不能为空';
      }
    }
    return null;
  }

  /**
   * 校验一条记录（对象 key→value）。
   * @returns {Array<string>} 错误数组（已含字段名）
   */
  function validateRecord(fields, values) {
    var errors = [];
    (fields || []).forEach(function (f) {
      if (f.type === 'table') {
        // 表格单独校验（必填）
        var e = validateField(f, values ? values[f.key] : undefined);
        if (e) errors.push(e);
        return;
      }
      var e2 = validateField(f, values ? values[f.key] : undefined);
      if (e2) errors.push(e2);
    });
    return errors;
  }

  /**
   * 校验批量记录（用于 Excel 导入）。
   * @returns {Array<{row:number, errors:string[]}>} 每条记录的错误（row 从 1 开始）
   */
  function validateBatch(fields, listOfValues) {
    return (listOfValues || []).map(function (vals, i) {
      return { row: i + 1, errors: validateRecord(fields, vals) };
    });
  }

  /** 单条记录的结构化校验：返回 [{key, label, message}] */
  function validateRecordStructured(fields, values) {
    var out = [];
    (fields || []).forEach(function (f) {
      var msg = validateField(f, values ? values[f.key] : undefined);
      if (msg) out.push({ key: f.key, label: f.label || f.key, message: msg });
    });
    return out;
  }

  /** 批量结构化校验：返回 [{row, errors:[{key,label,message}]}] */
  function validateBatchStructured(fields, listOfValues) {
    return (listOfValues || []).map(function (v, i) {
      return { row: i + 1, errors: validateRecordStructured(fields, v) };
    });
  }

  global.Validation = {
    validateField: validateField,
    validateRecord: validateRecord,
    validateBatch: validateBatch,
    validateRecordStructured: validateRecordStructured,
    validateBatchStructured: validateBatchStructured
  };
})(window);
