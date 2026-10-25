'use strict';
// Browser and Node share this rubric; it never calls the scientific verifier.
(function (root) {
  const VERSION = 'classroom-1.0.0';
  const LABELS = ['supported', 'contradicted', 'insufficient'];
  const exercise = (id, skill, claim, label, evidence, choices, explanation) =>
    ({id, skill, claim, label, evidence, choices, explanation});
  const BANK = [
    exercise('LT01', 'Ngày tháng', 'Hồ Chí Minh đọc Tuyên ngôn Độc lập ngày 2/9/1945.', 'supported', ['F001'], ['F001','F007','F026'], 'F001 ghi ngày 2/9/1945. Ngày trong nhận định khớp dữ kiện này.'),
    exercise('LT02', 'Nhân vật', 'Trần Văn Giàu đọc Tuyên ngôn Độc lập tại Quảng trường Ba Đình năm 1945.', 'contradicted', ['F002'], ['F002','F004','F014'], 'F002 xác định người đọc tại Ba Đình là Hồ Chí Minh. F004 nói về một lễ ở Sài Gòn; không thể chuyển vai trò giữa hai sự kiện.'),
    exercise('LT03', 'Giới hạn nguồn', 'Hồ Chí Minh thích màu xanh nhất khi chuẩn bị Lễ Độc lập năm 1945.', 'insufficient', ['F002'], ['F002','F004','F014'], 'F002 xác định nhân vật của sự kiện nhưng không ghi sở thích màu sắc. Thiếu thông tin trong kho không chứng minh nhận định sai ngoài thực tế.'),
    exercise('LT04', 'Địa điểm', 'Nguyễn Tất Thành ra đi tìm đường cứu nước từ Bến Nhà Rồng.', 'supported', ['F027'], ['F003','F027','F030'], 'F027 ghi Bến Nhà Rồng là địa điểm xuất phát. Đây là dữ kiện trực tiếp về địa điểm được hỏi.'),
    exercise('LT05', 'Ngày tháng', 'Khởi nghĩa giành chính quyền ở Hà Nội năm 1945 thắng lợi ngày 23/8/1945.', 'contradicted', ['F007'], ['F007','F009','F010'], 'F007 ghi ngày 19/8/1945 ở Hà Nội. Ngày 23/8/1945 của F009 thuộc Huế, nên không hỗ trợ nhận định về Hà Nội.'),
    exercise('LT06', 'Giới hạn nguồn', 'Chiến dịch Điện Biên Phủ bắt đầu ngày 13/3/1954 vì đó là ngày có thời tiết tốt nhất trong tháng.', 'insufficient', ['F015'], ['F015','F016','F018'], 'F015 hỗ trợ ngày bắt đầu, nhưng các dữ kiện được đưa ra không xác nhận lý do về thời tiết. Một phần đúng chưa đủ để hỗ trợ toàn bộ câu.'),
    exercise('LT07', 'Ngày tháng', 'Sắc lệnh số 76 hoãn tổng tuyển cử đến ngày 6/1/1946.', 'supported', ['F025'], ['F023','F024','F025'], 'Cần phân biệt ngày ban hành F023 với ngày tổng tuyển cử được hoãn đến F025. Nhận định khớp F025.'),
    exercise('LT08', 'Nhân vật', 'Nguyễn Ái Quốc chủ trì Hội nghị Trung ương lần thứ nhất tháng 10/1930.', 'contradicted', ['F022'], ['F020','F022','F032'], 'F022 xác định Trần Phú chủ trì Hội nghị tháng 10/1930. Nguyễn Ái Quốc ở F020/F032 gắn với các hội nghị khác.'),
    exercise('LT09', 'Giới hạn nguồn', 'Người ký Sắc lệnh số 76 đã dùng một cây bút mực xanh.', 'insufficient', ['F024'], ['F023','F024','F025'], 'F024 xác định người ký, không xác định loại bút hay màu mực. Cần thêm tài liệu mới có thể kết luận chi tiết này.'),
    exercise('LT10', 'Nhân vật', 'Nguyễn Ái Quốc chủ trì Hội nghị Trung ương VIII tháng 5/1941.', 'supported', ['F032'], ['F020','F022','F032'], 'F032 nêu đúng vai trò chủ trì và đúng Hội nghị Trung ương VIII. Trùng tên nhân vật ở một hội nghị khác chưa đủ làm bằng chứng.'),
    exercise('LT11', 'Địa điểm', 'Hội nghị Trung ương VIII tháng 5/1941 diễn ra tại Hương Cảng.', 'contradicted', ['F031'], ['F021','F030','F031'], 'F031 ghi Pác Bó, Cao Bằng. Hương Cảng trong F021 là địa điểm của hội nghị hợp nhất thành lập Đảng năm 1930.'),
    exercise('LT12', 'Giới hạn nguồn', 'Nguyễn Ái Quốc phát biểu đúng 45 phút khi chủ trì Hội nghị Trung ương VIII.', 'insufficient', ['F032'], ['F031','F032','F033'], 'F032 ghi vai trò chủ trì; kho không ghi thời lượng phát biểu. Không dùng sự vắng mặt của thông tin để kết luận thời lượng này sai.'),
    exercise('LT13', 'Nhiều dữ kiện', 'Chiến dịch Điện Biên Phủ bắt đầu ngày 13/3/1954 và kết thúc ngày 7/5/1954.', 'supported', ['F015','F016'], ['F015','F016','F018'], 'Cần cả F015 và F016 để hỗ trợ hai mốc thời gian. Chọn một dữ kiện sẽ bỏ sót nửa sau của nhận định.'),
    exercise('LT14', 'Nhiều dữ kiện', 'Nguyễn Ái Quốc trở về nước ngày 28/1/1941 tại Hà Nội.', 'contradicted', ['F030'], ['F029','F030','F031'], 'Ngày trong F029 khớp, nhưng F030 ghi tỉnh trở về là Cao Bằng. Chỉ cần một chi tiết trực tiếp mâu thuẫn đã đủ bác bỏ toàn bộ nhận định ghép này.'),
    exercise('LT15', 'Giới hạn nguồn', 'Nguyễn Tất Thành ra đi ngày 5/6/1911 vào một buổi sáng trời mưa.', 'insufficient', ['F026'], ['F026','F027','F028'], 'F026 hỗ trợ ngày xuất phát; kho không có dữ kiện về thời điểm trong ngày hay thời tiết. Giữ kết luận chưa đủ bằng chứng cho cả câu.')
  ];
  const fail = message => { throw new Error(message); };
  const record = value => value && typeof value === 'object' && !Array.isArray(value);
  const text = (value, min, max, field) => {
    if (typeof value !== 'string' || value.trim().length < min || value.length > max || /[\u0000-\u0008\u000b\u000c\u000e-\u001f]/.test(value)) fail(field + ' không hợp lệ.');
    return value.trim();
  };
  const identifier = value => {
    if (typeof value !== 'string' || !/^[a-zA-Z0-9_-]{3,80}$/.test(value)) fail('Mã bộ bài hoặc mã lượt làm không hợp lệ.');
    return value;
  };
  function validateBank(catalog) {
    const facts = new Set(catalog.facts.map(f => f.id));
    for (const e of BANK) {
      if (!LABELS.includes(e.label) || !e.evidence.length || e.evidence.some(id => !e.choices.includes(id)) || e.choices.some(id => !facts.has(id))) fail('Ngân hàng luyện tập không khớp kho nguồn.');
    }
    return true;
  }
  function assignment(value) {
    if (!record(value) || value.schema !== 'factguard-assignment-v1' || value.bank_version !== VERSION) fail('Bộ bài không đúng định dạng hoặc phiên bản. Tải lại bộ bài từ giáo viên.');
    const ids = value.exercise_ids;
    if (!Array.isArray(ids) || ids.length < 1 || ids.length > BANK.length || new Set(ids).size !== ids.length || ids.some(id => !BANK.some(e => e.id === id))) fail('Danh sách bài phải có 1–15 mã có trong ngân hàng, không trùng nhau.');
    return {schema:value.schema, bank_version:VERSION, id:identifier(value.id), title:text(value.title, 3, 120, 'Tên bộ bài'), exercise_ids:[...ids]};
  }
  function defaultAssignment() {
    return assignment({schema:'factguard-assignment-v1', bank_version:VERSION, id:'luyen-kiem-chung-01', title:'Đọc nguồn trước khi kết luận', exercise_ids:BANK.slice(0,6).map(e => e.id)});
  }
  const key = value => JSON.stringify([value.bank_version, value.id, value.title, value.exercise_ids]);
  function response(value, expectedId) {
    const e = BANK.find(e => e.id === expectedId);
    if (!record(value) || !e || value.exercise_id !== expectedId || !LABELS.includes(value.label)) fail('Câu trả lời không đúng bài hoặc nhãn.');
    const ids = value.evidence_ids;
    if (!Array.isArray(ids) || !ids.length || ids.length > e.choices.length || new Set(ids).size !== ids.length || ids.some(id => !e.choices.includes(id))) fail('Chọn ít nhất một dữ kiện trong phiếu, không lặp mã.');
    if (![50,75,100].includes(value.confidence)) fail('Mức chắc chắn phải là 50, 75 hoặc 100.');
    return {exercise_id:e.id, label:value.label, evidence_ids:[...ids].sort(), confidence:value.confidence, reason:text(value.reason,20,600,'Giải thích (20–600 ký tự)')};
  }
  function grade(value) {
    const r = response(value, value?.exercise_id), e = BANK.find(e => e.id === r.exercise_id);
    const label_correct = r.label === e.label;
    const evidence_correct = JSON.stringify(r.evidence_ids) === JSON.stringify([...e.evidence].sort());
    return {...r, expected_label:e.label, expected_evidence:[...e.evidence], label_correct, evidence_correct, points:2*Number(label_correct)+Number(evidence_correct), explanation:e.explanation, skill:e.skill};
  }
  function report(value) {
    if (!record(value) || value.schema !== 'factguard-attempt-v1' || value.bank_version !== VERSION) fail('Phiếu kết quả sai định dạng hoặc khác phiên bản ngân hàng.');
    const a = assignment(value.assignment);
    if (!Array.isArray(value.responses) || value.responses.length !== a.exercise_ids.length) fail('Chỉ nhận phiếu đã hoàn tất toàn bộ bộ bài.');
    for (const name of ['started_at','completed_at']) if (typeof value[name] !== 'string' || !/^\d{4}-\d{2}-\d{2}T/.test(value[name]) || !Number.isFinite(Date.parse(value[name]))) fail('Thời gian trong phiếu không hợp lệ.');
    if (Date.parse(value.completed_at) < Date.parse(value.started_at)) fail('Thời gian hoàn tất sớm hơn thời gian bắt đầu.');
    return {schema:value.schema, bank_version:VERSION, attempt_id:identifier(value.attempt_id), assignment:a, started_at:value.started_at, completed_at:value.completed_at, responses:value.responses.map((r,i) => response(r,a.exercise_ids[i]))};
  }
  function summarize(value) {
    const r = report(value), rows = r.responses.map(grade);
    return {report:r, rows, count:rows.length, points:rows.reduce((s,r) => s+r.points,0), max_points:3*rows.length, label_correct:rows.filter(r => r.label_correct).length, evidence_correct:rows.filter(r => r.evidence_correct).length, confident_errors:rows.filter(r => !r.label_correct && r.confidence >= 75).length};
  }
  function aggregate(values) {
    if (!Array.isArray(values) || !values.length || values.length > 200) fail('Chọn từ 1 đến 200 phiếu.');
    const unique = new Map(); let duplicates = 0, selectedKey;
    for (const value of values) {
      const r = report(value), k = key(r.assignment);
      if (selectedKey && selectedKey !== k) fail('Các phiếu thuộc bộ bài khác nhau. Chỉ tổng hợp cùng mã, tên, phiên bản và thứ tự bài.');
      selectedKey = k;
      if (unique.has(r.attempt_id)) {
        if (JSON.stringify(unique.get(r.attempt_id)) !== JSON.stringify(r)) fail('Có hai nội dung khác nhau cùng mã lượt làm. Kiểm tra tệp trước khi nhập.');
        duplicates++; continue;
      }
      unique.set(r.attempt_id,r);
    }
    const summaries = [...unique.values()].map(summarize), rows = summaries.flatMap(s => s.rows);
    const matrix = LABELS.map(gold => LABELS.map(pred => rows.filter(r => r.expected_label === gold && r.label === pred).length));
    return {assignment:summaries[0].report.assignment, reports:[...unique.values()], summaries, duplicates, attempts:unique.size, count:rows.length, label_correct:rows.filter(r => r.label_correct).length, evidence_correct:rows.filter(r => r.evidence_correct).length, confident_errors:rows.filter(r => !r.label_correct && r.confidence >= 75).length, matrix, by_exercise:summaries[0].report.assignment.exercise_ids.map(id => {const items=rows.filter(r => r.exercise_id === id);return {id, count:items.length, label_correct:items.filter(r => r.label_correct).length, evidence_correct:items.filter(r => r.evidence_correct).length};})};
  }
  function csvCell(value) {
    let s = String(value ?? '');
    if (/^[\s]*[=+@-]/.test(s) || /^[\t\r\n]/.test(s)) s = "'" + s;
    return '"' + s.replace(/"/g,'""') + '"';
  }
  function csv(rows) { return '\ufeff' + rows.map(r => r.map(csvCell).join(',')).join('\r\n'); }
  const api = {VERSION, LABELS, BANK, validateBank, assignment, defaultAssignment, key, response, grade, report, summarize, aggregate, csv};
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.FactGuardClassroom = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
