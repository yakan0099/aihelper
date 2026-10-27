export function related(memories, scope) {
  return memories.filter(m => !m.deleted && m.scope === scope.trim()).sort((a,b)=>b.updated-a.updated).slice(0,5);
}
export function mergeMemories(local, remote) {
  const map = new Map();
  for (const m of [...local,...remote]) {
    const old=map.get(m.id);
    if (!old || m.updated>old.updated || (m.updated===old.updated && m.deleted)) map.set(m.id,m);
  }
  return [...map.values()];
}
export function guard(previous, current, now=Date.now()) {
  return !!previous?.answer && previous.window_id===current.window_id && previous.fingerprint===current.fingerprint && now-previous.created>=0 && now-previous.created<300000;
}
export function demo(text, memories) {
  return {observation:'데모: 이미지 이해를 수행하지 않았습니다.',summary:'본문 발췌 (AI 요약 아님)\n'+(text.slice(0,1200)||'본문을 붙여넣어 기억 흐름을 시험하세요.'),next_action:'내용을 확인하고 교정을 저장하세요.',corrections:memories.map(m=>m.correction)};
}
export function formatAnswer(r) {
  return `${r.observation}\n\n${r.summary}\n\n다음 행동: ${r.next_action}`+(r.corrections?.length?'\n\n불러온 사용자 교정:\n'+r.corrections.join('\n'):'');
}
