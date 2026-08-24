/* ============================================================
 * printer.js — 字段替换 + 页面拼装 + 预览/打印
 * 全局对象：Printer
 * 依赖：Fields
 * ========================================================== */
(function (global) {
  'use strict';

  function buildTable(headers, rows, border) {
    var headers2 = headers && headers.length ? headers : [];
    var th = headers2.map(function (h) {
      return '<th style="padding:5px 8px;border-bottom:2px solid #444;font-weight:600;background:#f3f3f3">' + Fields.esc(h) + '</th>';
    }).join('');
    var tr = rows.map(function (r) {
      return '<tr>' + headers2.map(function (h, i) {
        var v = (r && r[i] != null) ? r[i] : '';
        return '<td style="padding:5px 8px">' + Fields.esc(v) + '</td>';
      }).join('') + '</tr>';
    }).join('');
    var style = border ? 'border-collapse:collapse;width:100%;margin:6px 0;font-size:0.92em' :
                           'border-collapse:collapse;width:100%;margin:6px 0;font-size:0.92em';
    return '<table class="data-table" style="' + style + '">' +
      (th ? '<thead><tr>' + th + '</tr></thead>' : '') +
      '<tbody>' + tr + '</tbody></table>';
  }

  /** 将模板正文中的 {{key}} 替换为用户提供的值 */
  function fillTokens(html, tpl, values) {
    return html.replace(Fields.TOKEN_RE, function (m, key) {
      var f = null;
      for (var i = 0; i < tpl.fields.length; i++) if (tpl.fields[i].key === key) { f = tpl.fields[i]; break; }
      if (!f) return m; // 未知占位符保留原样
      if (f.type === 'table') {
        var d = values[key];
        if (d && d.headers && d.rows && d.rows.length) return buildTable(d.headers, d.rows, tpl.settings.tableBorder);
        return '<span class="empty-table">（未提供表格数据）</span>';
      }
      var v = values[key];
      if (v === undefined || v === null || v === '') {
        if (f.default) return Fields.esc(f.default);
        return '';
      }
      return Fields.esc(v);
    });
  }

  function documentShell(tpl, bodyHtml) {
    var s = tpl.settings || {};
    var pageSize = s.pageSize || 'A4';
    var orient = s.orientation || 'portrait';
    var margin = (s.marginTop || 15) + 'mm ' + (s.marginRight || 15) + 'mm ' +
                 (s.marginBottom || 15) + 'mm ' + (s.marginLeft || 15) + 'mm';
    var header = s.headerText ? Fields.esc(s.headerText) : '';
    var footer = s.footerText ? Fields.esc(s.footerText) : '';
    var css =
      '@page { size: ' + pageSize + ' ' + orient + '; margin: ' + margin + '; }\n' +
      '* { box-sizing: border-box; }\n' +
      'html,body { margin:0; padding:0; }\n' +
      'body { font-family: ' + (s.fontFamily || 'sans-serif') + '; font-size: ' + (s.fontSize || 14) + 'px; ' +
        'line-height: ' + (s.lineHeight || 1.6) + '; color:#000; }\n' +
      'h1,h2,h3,h4,h5,h6 { margin: 6px 0; text-indent: 0; }\n' +
      'p, div, li { margin: 4px 0; text-indent: 2em; }\n' +
      // Word 风格首行缩进：仅对正文段落生效，标题/表格/署名/.no-indent 不缩进
      '.no-indent { text-indent: 0 !important; }\n' +
      'table { border-collapse: collapse; text-indent: 0; }\n' +
      'td,th { vertical-align: top; text-indent: 0; }\n' +
      '.doc-header { position: fixed; top:0; left:0; right:0; text-align:' + (s.headerAlign || 'center') +
        '; font-weight:600; font-size:1.05em; }\n' +
      '.doc-footer { position: fixed; bottom:0; left:0; right:0; text-align:' + (s.footerAlign || 'center') +
        '; font-size:0.82em; color:#555; }\n' +
      '.doc-body { }\n' +
      '.data-table th, .data-table td { border:1px solid #666; }\n' +
      '.data-table { border:1px solid #666; }\n' +
      '.empty-table { color:#c00; font-size:0.9em; }\n' +
      '.page-break { page-break-before: always; }\n';
    return '<!DOCTYPE html><html><head><meta charset="utf-8"><title>' +
      Fields.esc(tpl.name || '打印') + '</title><style>' + css + '</style></head>' +
      '<body>' +
      '<div class="doc-header">' + header + '</div>' +
      '<div class="doc-footer">' + footer + '</div>' +
      '<div class="doc-body">' + bodyHtml + '</div>' +
      '</body></html>';
  }

  /** 根据一份 values 渲染完整打印文档 HTML */
  function renderOne(tpl, values) {
    var body = fillTokens(tpl.content || '', tpl, values || {});
    return documentShell(tpl, body);
  }

  /** 批量：多份 values，用分页符连接（表头/页脚自动每页重复） */
  function renderMulti(tpl, listOfValues) {
    var bodies = listOfValues.map(function (v, i) {
      var b = fillTokens(tpl.content || '', tpl, v || {});
      return (i === 0 ? '' : '<div class="page-break"></div>') + b;
    });
    return documentShell(tpl, bodies.join(''));
  }

  /** 写入 iframe 并在加载后调整 header/footer 与正文的间距 */
  function mountInIframe(iframe, html, cb) {
    function onLoad() {
      try {
        var doc = iframe.contentDocument || iframe.contentWindow.document;
        var header = doc.querySelector('.doc-header');
        var footer = doc.querySelector('.doc-footer');
        var body = doc.querySelector('.doc-body');
        var pt = (header && header.offsetHeight) ? header.offsetHeight + 10 : 0;
        var pb = (footer && footer.offsetHeight) ? footer.offsetHeight + 10 : 0;
        if (body) { body.style.paddingTop = pt + 'px'; body.style.paddingBottom = pb + 'px'; }
      } catch (e) { /* 跨域等忽略 */ }
      if (cb) cb();
    }
    if (iframe.contentDocument && iframe.contentDocument.readyState === 'complete') {
      // 直接写
    }
    iframe.onload = onLoad;
    var d = iframe.contentDocument || (iframe.contentWindow && iframe.contentWindow.document);
    if (!d) { iframe.srcdoc = html; return; }
    d.open(); d.write(html); d.close();
    // onload 在某些浏览器对 srcdoc 才触发，这里再次保险调用
    setTimeout(onLoad, 60);
  }

  /** 预览：渲染到可见 iframe */
  function showPreview(iframe, tpl, values) {
    var html = renderOne(tpl, values);
    mountInIframe(iframe, html);
  }

  /** 打印单份（创建隐藏 iframe） */
  function printOne(tpl, values) {
    var html = renderOne(tpl, values);
    doPrint(html);
  }

  /** 打印多份（批量） */
  function printMulti(tpl, listOfValues) {
    var html = renderMulti(tpl, listOfValues);
    doPrint(html);
  }

  function doPrint(html) {
    var iframe = document.createElement('iframe');
    iframe.style.position = 'fixed';
    iframe.style.right = '0';
    iframe.style.bottom = '0';
    iframe.style.width = '0';
    iframe.style.height = '0';
    iframe.style.border = '0';
    document.body.appendChild(iframe);
    function run() {
      try {
        var doc = iframe.contentDocument || iframe.contentWindow.document;
        var header = doc.querySelector('.doc-header');
        var footer = doc.querySelector('.doc-footer');
        var body = doc.querySelector('.doc-body');
        var pt = (header && header.offsetHeight) ? header.offsetHeight + 10 : 0;
        var pb = (footer && footer.offsetHeight) ? footer.offsetHeight + 10 : 0;
        if (body) { body.style.paddingTop = pt + 'px'; body.style.paddingBottom = pb + 'px'; }
        iframe.contentWindow.focus();
        iframe.contentWindow.print();
      } catch (e) { console.warn(e); }
      setTimeout(function () { if (iframe.parentNode) iframe.parentNode.removeChild(iframe); }, 1500);
    }
    var d = iframe.contentDocument || (iframe.contentWindow && iframe.contentWindow.document);
    d.open(); d.write(html); d.close();
    setTimeout(run, 200);
  }

  global.Printer = {
    renderOne: renderOne,
    renderMulti: renderMulti,
    showPreview: showPreview,
    printOne: printOne,
    printMulti: printMulti,
    buildTable: buildTable
  };
})(window);
