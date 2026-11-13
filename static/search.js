(function(){
  var root = window.ARCHIVE_ROOT || '';
  var index = null;
  function load(cb){ if(index) return cb(index);
    fetch(root + 'assets/search-index.json').then(function(r){return r.json();}).then(function(d){index=d;cb(d);}); }
  function score(item, terms){
    var t = item.t.toLowerCase(), x = (item.x + ' ' + item.h + ' ' + (item.c||'')).toLowerCase(), s = 0;
    for (var i=0;i<terms.length;i++){ var q = terms[i];
      if (t === q) s += 50; else if (t.indexOf(q) === 0) s += 20; else if (t.indexOf(q) >= 0) s += 12;
      else if (x.indexOf(q) >= 0) s += 3; else return 0; }
    return s; }
  function search(q, cb){ var terms = q.toLowerCase().split(/\s+/).filter(Boolean); if(!terms.length) return cb([]);
    load(function(d){ cb(d.map(function(it){return [score(it,terms),it];}).filter(function(p){return p[0]>0;})
      .sort(function(a,b){return b[0]-a[0];}).map(function(p){return p[1];})); }); }
  function esc(s){return String(s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
  var input = document.getElementById('q'), box = document.getElementById('search-results');
  if (input && box){
    input.addEventListener('input', function(){ var q = input.value.trim(); if(!q){box.style.display='none';return;}
      search(q, function(r){ box.innerHTML = r.slice(0,8).map(function(it){return '<a href="'+root+it.u+'"><small>'+esc(it.c||'')+'</small>'+esc(it.t)+'</a>';}).join('') || '<a>No articles found</a>';
        box.style.display='block'; }); });
    document.addEventListener('click', function(e){ if(!box.contains(e.target) && e.target!==input) box.style.display='none'; });
  }
  var page = document.getElementById('search-page-results');
  if (page){ var q = new URLSearchParams(location.search).get('q') || ''; if (input) input.value = q;
    search(q, function(r){ document.getElementById('search-summary').textContent = q ? (r.length + ' results for “' + q + '”') : 'Search the archive by title or text.';
      page.innerHTML = r.map(function(it){return '<div class="result"><small>'+esc(it.c||'')+'</small><a href="'+root+it.u+'">'+esc(it.t)+'</a><p>'+esc(it.x.slice(0,240))+'…</p></div>';}).join(''); }); }
})();
