document.addEventListener('DOMContentLoaded', function () {
  const rankingModeGroup = document.getElementById('rankingModeGroup');
  const modeRegular = document.getElementById('modeRegular');
  const modeAggregate = document.getElementById('modeAggregate');

  function toggleRankingMode() {
    if (modeAggregate && rankingModeGroup && modeAggregate.checked) {
      rankingModeGroup.style.display = '';
    } else if (rankingModeGroup) {
      rankingModeGroup.style.display = 'none';
    }
  }

  if (modeRegular && modeAggregate) {
    modeRegular.addEventListener('change', toggleRankingMode);
    modeAggregate.addEventListener('change', toggleRankingMode);
    toggleRankingMode();
  }
});