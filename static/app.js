/**
 * SnapSheet (拍表) - Frontend Application
 * 酒店手写表单OCR识别前端
 */
(function () {
  "use strict";

  const API_BASE = "/api/v1";

  // DOM elements
  const imageInput = document.getElementById("imageInput");
  const uploadArea = document.getElementById("uploadArea");
  const previewContainer = document.getElementById("previewContainer");
  const previewImage = document.getElementById("previewImage");
  const btnClearImage = document.getElementById("btnClearImage");
  const templateSelect = document.getElementById("templateSelect");
  const language = document.getElementById("language");
  const btnRecognize = document.getElementById("btnRecognize");
  const stepResult = document.getElementById("step-result");
  const loading = document.getElementById("loading");
  const resultContent = document.getElementById("resultContent");
  const resultCount = document.getElementById("resultCount");
  const resultConfidence = document.getElementById("resultConfidence");
  const resultBody = document.getElementById("resultBody");
  const resultTable = document.getElementById("resultTable");
  const tablePreviewWrapper = document.getElementById("tablePreviewWrapper");
  const tablePreview = document.getElementById("tablePreview");
  const btnDownload = document.getElementById("btnDownload");
  const btnDownloadRaw = document.getElementById("btnDownloadRaw");
  const btnEmail = document.getElementById("btnEmail");
  const emailModal = document.getElementById("emailModal");
  const emailInput = document.getElementById("emailInput");
  const btnSendEmail = document.getElementById("btnSendEmail");
  const btnCloseModal = document.getElementById("btnCloseModal");
  const btnUploadTemplate = document.getElementById("btnUploadTemplate");

  let selectedFiles = [];
  let currentTaskId = null;
  let currentHasRaw = false;

  // ===== Custom Select Component =====
  function initCustomSelect(wrapperEl, hiddenSelect) {
    const display = wrapperEl.querySelector(".select-display");
    const dropdown = wrapperEl.querySelector(".select-dropdown");

    display.addEventListener("click", function (e) {
      e.stopPropagation();
      // Close other open selects
      document.querySelectorAll(".custom-select.open").forEach(function (el) {
        if (el !== wrapperEl) el.classList.remove("open");
      });
      wrapperEl.classList.toggle("open");
    });

    dropdown.addEventListener("click", function (e) {
      var option = e.target.closest(".select-option");
      if (!option) return;
      e.stopPropagation();

      // Update visual state
      dropdown.querySelectorAll(".select-option").forEach(function (o) {
        o.classList.remove("selected");
      });
      option.classList.add("selected");
      display.querySelector("span").textContent = option.textContent;

      // Sync hidden select
      hiddenSelect.value = option.dataset.value;

      wrapperEl.classList.remove("open");
    });
  }

  // Close dropdowns on outside click
  document.addEventListener("click", function () {
    document.querySelectorAll(".custom-select.open").forEach(function (el) {
      el.classList.remove("open");
    });
  });

  // Init language select
  initCustomSelect(
    document.getElementById("languageSelectWrapper"),
    language
  );

  // Init template select
  var templateWrapper = document.getElementById("templateSelectWrapper");
  var templateDropdown = document.getElementById("templateDropdown");
  var templateDisplay = document.getElementById("templateDisplay");
  initCustomSelect(templateWrapper, templateSelect);

  // ===== Template file input display =====
  var templateFileInput = document.getElementById("templateFile");
  var templateFileDisplay = document.getElementById("templateFileDisplay");
  if (templateFileInput && templateFileDisplay) {
    templateFileInput.addEventListener("change", function () {
      if (templateFileInput.files.length > 0) {
        templateFileDisplay.textContent = templateFileInput.files[0].name;
      } else {
        templateFileDisplay.innerHTML =
          '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12"/></svg> 选择文件 / Choose file';
      }
    });
  }

  // ===== Image Upload =====
  imageInput.addEventListener("change", function (e) {
    const files = Array.from(e.target.files);
    if (files.length === 0) return;

    selectedFiles = files;
    const reader = new FileReader();
    reader.onload = function (ev) {
      previewImage.src = ev.target.result;
      previewContainer.style.display = "block";
      uploadArea.style.display = "none";
      btnRecognize.disabled = false;
    };
    reader.readAsDataURL(files[0]);
  });

  btnClearImage.addEventListener("click", function () {
    selectedFiles = [];
    imageInput.value = "";
    previewContainer.style.display = "none";
    uploadArea.style.display = "block";
    btnRecognize.disabled = true;
    stepResult.style.display = "none";
  });

  // ===== Load Templates =====
  async function loadTemplates() {
    try {
      const resp = await fetch(`${API_BASE}/templates/`);
      const data = await resp.json();
      // 清空下拉框（保留第一项"自动识别"）
      while (templateSelect.options.length > 1) {
        templateSelect.remove(1);
      }
      // 清空自定义下拉选项（保留第一项）
      while (templateDropdown.children.length > 1) {
        templateDropdown.removeChild(templateDropdown.lastChild);
      }
      // 重置显示文本
      templateDisplay.querySelector("span").textContent = "自动识别 / Auto detect";
      templateDropdown.querySelector(".select-option").classList.add("selected");

      // 清空模板列表
      var templateList = document.getElementById("templateList");
      templateList.innerHTML = "";

      if (data.code === 0 && Array.isArray(data.data) && data.data.length > 0) {
        data.data.forEach(function (t) {
          var label = t.name + (t.description ? " - " + t.description : "");

          // 添加到隐藏的原生select
          var opt = document.createElement("option");
          opt.value = t.template_id;
          opt.textContent = label;
          templateSelect.appendChild(opt);

          // 添加到自定义下拉
          var div = document.createElement("div");
          div.className = "select-option";
          div.dataset.value = t.template_id;
          div.textContent = label;
          templateDropdown.appendChild(div);

          // 添加到模板管理列表
          var item = document.createElement("div");
          item.className = "template-item";

          var info = document.createElement("span");
          info.className = "template-info";
          info.textContent = label;
          info.style.cursor = "pointer";
          info.title = "点击预览 / Click to preview";
          info.addEventListener("click", function () {
            previewTemplate(t.template_id, t.name);
          });

          var btnDel = document.createElement("button");
          btnDel.className = "btn-delete";
          btnDel.textContent = "删除";
          btnDel.setAttribute("data-id", t.template_id);
          btnDel.addEventListener("click", function () {
            deleteTemplate(t.template_id, t.name);
          });

          item.appendChild(info);
          item.appendChild(btnDel);
          templateList.appendChild(item);
        });
      } else {
        templateList.innerHTML = '<div class="template-empty">暂无模板 / No templates</div>';
      }
    } catch (e) {
      // Templates not loaded - non-critical
    }
  }

  // ===== Delete Template =====
  async function deleteTemplate(templateId, name) {
    if (!confirm("确认删除模板 \"" + name + "\"？\nDelete template \"" + name + "\"?")) {
      return;
    }
    try {
      var resp = await fetch(API_BASE + "/templates/" + templateId, {
        method: "DELETE",
      });
      var data = await resp.json();
      if (data.code === 0) {
        showToast("模板已删除 / Template deleted");
        loadTemplates();
      } else {
        showToast("删除失败: " + data.message);
      }
    } catch (e) {
      showToast("删除失败: " + e.message);
    }
  }

  // ===== Template Preview =====
  var templatePreviewModal = document.getElementById("templatePreviewModal");
  var templatePreviewTitle = document.getElementById("templatePreviewTitle");
  var templatePreviewContent = document.getElementById("templatePreviewContent");
  var btnClosePreview = document.getElementById("btnClosePreview");

  async function previewTemplate(templateId, name) {
    templatePreviewTitle.textContent = name;
    templatePreviewContent.innerHTML = '<div class="spinner"></div>';
    templatePreviewModal.style.display = "flex";

    try {
      var resp = await fetch(API_BASE + "/templates/" + templateId + "/preview");
      var data = await resp.json();
      if (data.code === 0 && data.data && data.data.html) {
        var html = data.data.html;
        if (data.data.truncated) {
          html += '<p class="preview-hint" style="margin-top:8px;">仅显示前 ' + data.data.row_count + ' 行 / First ' + data.data.row_count + ' rows shown</p>';
        }
        templatePreviewContent.innerHTML = html;
      } else {
        templatePreviewContent.innerHTML = '<p class="preview-hint">无法加载预览 / Preview unavailable</p>';
      }
    } catch (e) {
      templatePreviewContent.innerHTML = '<p class="preview-hint">加载失败 / Load failed</p>';
    }
  }

  btnClosePreview.addEventListener("click", function () {
    templatePreviewModal.style.display = "none";
  });
  templatePreviewModal.addEventListener("click", function (e) {
    if (e.target === templatePreviewModal) {
      templatePreviewModal.style.display = "none";
    }
  });

  // ===== OCR Recognition =====
  btnRecognize.addEventListener("click", async function () {
    if (selectedFiles.length === 0) return;

    stepResult.style.display = "block";
    loading.style.display = "block";
    resultContent.style.display = "none";
    btnRecognize.disabled = true;

    stepResult.scrollIntoView({ behavior: "smooth" });

    try {
      const formData = new FormData();
      formData.append("image", selectedFiles[0]);
      if (templateSelect.value) {
        formData.append("template_id", templateSelect.value);
      }
      formData.append("language", language.value);

      const resp = await fetch(`${API_BASE}/ocr/recognize`, {
        method: "POST",
        body: formData,
      });

      const data = await resp.json();

      if (data.code === 0 && data.data) {
        currentTaskId = data.data.task_id;
        currentHasRaw = !!data.data.raw_output_file;
        renderResult(data.data);
      } else {
        showToast("识别失败: " + (data.message || "Unknown error"));
      }
    } catch (e) {
      showToast("网络错误: " + e.message);
    } finally {
      loading.style.display = "none";
      btnRecognize.disabled = false;
    }
  });

  function renderResult(data) {
    resultContent.style.display = "block";
    const items = data.items || [];
    const tableHtml = data.table_html || [];

    if (tableHtml.length > 0) {
      tablePreviewWrapper.style.display = "block";
      resultTable.style.display = "none";

      resultCount.textContent = "识别 " + (data.table_count || tableHtml.length) + " 个表格";
      resultConfidence.textContent = "识别 " + items.length + " 个字段";

      var safeHtml = "";
      tableHtml.forEach(function (html, idx) {
        if (tableHtml.length > 1) {
          safeHtml += '<div class="table-label">表格 ' + (idx + 1) + ' / Table ' + (idx + 1) + '</div>';
        }
        safeHtml += sanitizeTableHtml(html);
      });
      tablePreview.innerHTML = safeHtml;
    } else {
      tablePreviewWrapper.style.display = "none";
      resultTable.style.display = "table";

      resultCount.textContent = "识别 " + items.length + " 个字段";
      var avgConf =
        items.length > 0
          ? items.reduce(function (s, i) { return s + i.confidence; }, 0) / items.length
          : 0;
      resultConfidence.textContent = "平均置信度: " + (avgConf * 100).toFixed(1) + "%";

      resultBody.innerHTML = "";
      items.forEach(function (item) {
        var tr = document.createElement("tr");

        var tdField = document.createElement("td");
        tdField.textContent = item.field_name;

        var tdValue = document.createElement("td");
        tdValue.textContent = item.value;

        var tdConf = document.createElement("td");
        var confPct = (item.confidence * 100).toFixed(0);
        tdConf.textContent = confPct + "%";
        if (item.confidence >= 0.9) tdConf.className = "conf-high";
        else if (item.confidence >= 0.7) tdConf.className = "conf-mid";
        else tdConf.className = "conf-low";

        tr.appendChild(tdField);
        tr.appendChild(tdValue);
        tr.appendChild(tdConf);
        resultBody.appendChild(tr);
      });
    }
  }

  /**
   * 安全处理HTML表格：只保留表格相关标签和属性
   */
  function sanitizeTableHtml(html) {
    var allowedTags = ["table", "thead", "tbody", "tfoot", "tr", "th", "td", "br", "caption"];
    var allowedAttrs = ["colspan", "rowspan", "class"];

    var parser = new DOMParser();
    var doc = parser.parseFromString("<div>" + html + "</div>", "text/html");
    var container = doc.body.firstChild;

    function cleanNode(node) {
      if (node.nodeType === 3) return document.createTextNode(node.textContent);
      if (node.nodeType !== 1) return null;

      var tagName = node.tagName.toLowerCase();
      if (allowedTags.indexOf(tagName) === -1) {
        var frag = document.createDocumentFragment();
        for (var i = 0; i < node.childNodes.length; i++) {
          var child = cleanNode(node.childNodes[i]);
          if (child) frag.appendChild(child);
        }
        return frag;
      }

      var el = document.createElement(tagName);
      for (var j = 0; j < allowedAttrs.length; j++) {
        var attr = allowedAttrs[j];
        if (node.hasAttribute(attr)) {
          el.setAttribute(attr, node.getAttribute(attr));
        }
      }
      if (tagName === "table") {
        el.className = "ocr-table-preview";
      }

      for (var k = 0; k < node.childNodes.length; k++) {
        var child = cleanNode(node.childNodes[k]);
        if (child) el.appendChild(child);
      }
      return el;
    }

    var cleaned = cleanNode(container);
    var wrapper = document.createElement("div");
    wrapper.appendChild(cleaned);
    return wrapper.innerHTML;
  }

  // ===== Download =====
  var downloadModal = document.getElementById("downloadModal");
  var downloadFilename = document.getElementById("downloadFilename");
  var btnConfirmDownload = document.getElementById("btnConfirmDownload");
  var btnCloseDownload = document.getElementById("btnCloseDownload");

  btnDownload.addEventListener("click", function () {
    if (!currentTaskId) return;
    downloadFilename.value = "";
    downloadModal.style.display = "flex";
    downloadFilename.focus();
  });

  btnDownloadRaw.addEventListener("click", function () {
    if (!currentTaskId) return;
    window.location.href = API_BASE + "/ocr/download/" + currentTaskId + "?raw=true";
  });

  btnCloseDownload.addEventListener("click", function () {
    downloadModal.style.display = "none";
  });

  btnConfirmDownload.addEventListener("click", function () {
    if (!currentTaskId) return;
    var name = downloadFilename.value.trim();
    var url = API_BASE + "/ocr/download/" + currentTaskId;
    if (name) {
      url += "?filename=" + encodeURIComponent(name);
    }
    window.location.href = url;
    downloadModal.style.display = "none";
  });

  // ===== Email =====
  btnEmail.addEventListener("click", function () {
    emailModal.style.display = "flex";
    emailInput.focus();
  });

  btnCloseModal.addEventListener("click", function () {
    emailModal.style.display = "none";
  });

  btnSendEmail.addEventListener("click", async function () {
    const email = emailInput.value.trim();
    if (!email || !currentTaskId) return;

    btnSendEmail.disabled = true;
    btnSendEmail.textContent = "发送中...";

    try {
      const formData = new FormData();
      formData.append("task_id", currentTaskId);
      formData.append("to_email", email);

      const resp = await fetch(`${API_BASE}/ocr/send-email`, {
        method: "POST",
        body: formData,
      });
      const data = await resp.json();

      if (data.code === 0) {
        showToast("邮件已发送 / Email sent!");
        emailModal.style.display = "none";
      } else {
        showToast("发送失败: " + data.message);
      }
    } catch (e) {
      showToast("发送失败: " + e.message);
    } finally {
      btnSendEmail.disabled = false;
      btnSendEmail.textContent = "发送 / Send";
    }
  });

  // ===== Template Upload =====
  btnUploadTemplate.addEventListener("click", async function () {
    const name = document.getElementById("templateName").value.trim();
    const desc = document.getElementById("templateDesc").value.trim();
    const fileInput = document.getElementById("templateFile");
    const file = fileInput.files[0];

    if (!name || !file) {
      showToast("请填写模板名称并选择文件");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);
    formData.append("name", name);
    formData.append("description", desc);

    try {
      const resp = await fetch(`${API_BASE}/templates/upload`, {
        method: "POST",
        body: formData,
      });
      const data = await resp.json();
      if (data.code === 0) {
        showToast("模板上传成功 / Template uploaded!");
        loadTemplates();
      } else {
        showToast("上传失败: " + data.message);
      }
    } catch (e) {
      showToast("上传失败: " + e.message);
    }
  });

  // ===== Toast =====
  function showToast(msg) {
    let toast = document.querySelector(".toast");
    if (!toast) {
      toast = document.createElement("div");
      toast.className = "toast";
      document.body.appendChild(toast);
    }
    toast.textContent = msg;
    toast.classList.add("show");
    setTimeout(function () {
      toast.classList.remove("show");
    }, 3000);
  }

  // ===== Init =====
  loadTemplates();
})();
