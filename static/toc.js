(function(){
  var links = Array.prototype.slice.call(document.querySelectorAll('.toc a'));
  var targets = links.map(function(a){ return document.getElementById(a.getAttribute('href').slice(1)); });
  function update(){ var y = window.scrollY + 120, on = 0;
    targets.forEach(function(t,i){ if(t && t.getBoundingClientRect().top + window.scrollY <= y) on = i; });
    links.forEach(function(a,i){ a.classList.toggle('on', i===on); }); }
  window.addEventListener('scroll', update, {passive:true}); update();
})();
