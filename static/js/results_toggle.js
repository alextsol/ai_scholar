document.addEventListener('DOMContentLoaded', function () {
  const resultLimitGroup = document.getElementById('resultLimitGroup');
  const aiResultLimitGroup = document.getElementById('aiResultLimitGroup');
  const modeRegular = document.getElementById('modeRegular');
  const modeAggregate = document.getElementById('modeAggregate');

  function toggleResultInputs() {
    if (modeRegular && resultLimitGroup) {
      resultLimitGroup.style.display = modeRegular.checked ? '' : 'none';
    }
    if (modeAggregate && aiResultLimitGroup) {
      aiResultLimitGroup.style.display = modeAggregate.checked ? '' : 'none';
    }
  }

  if (modeRegular && modeAggregate) {
    modeRegular.addEventListener('change', toggleResultInputs);
    modeAggregate.addEventListener('change', toggleResultInputs);
    toggleResultInputs();
  }
});