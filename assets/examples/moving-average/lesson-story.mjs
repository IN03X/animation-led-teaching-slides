const R = String.raw;
const rule = R`y[n]=\frac{x[n]+x[n-1]}{2}`;
const values = [0, 0, 2, 4, 2, 0];

export async function content(a) {
  a.navigationAliases = {'lesson-map':'overview', 'band-map':'overview', 'recover-map':'overview', 'course':'overview'};
  const route = () => {
    a.text('input-label', 'Input', 90, 110, 180, 28, 22, false, 'center');
    a.eq('input-symbol', 'x[n]', 90, 145, 180, 45, 34, 'center');
    a.arrow('to-average', 290, 163, 150);
    a.block('average-operation', 'Average a pair', 462, 137, 350, 57);
    a.arrow('to-output', 835, 163, 150);
    a.text('output-label', 'Output', 1010, 110, 180, 28, 22, false, 'center');
    a.eq('output-symbol', 'y[n]', 1010, 145, 180, 45, 34, 'center');
  };
  const page = (id, title, sub, note, purpose) => {
    a.page(id, title, sub, null, note, {bare:true, purpose, parent:'overview'});
    route();
  };
  const result = (name, tex, stage = 0, y = 623) => a.reveal(stage, () => {
    a.statement(name, tex, 64, y, 1144, 67, 35);
    a.line(name + '-emphasis', 64, y + 69, 1144, '#777777', 1.2);
  });

  page('overview', 'Two-point moving average', 'The known input',
    'The index n locates an individual sample in the sequence x. The five supplied samples run from n=0 to n=4. The extra value x[-1]=0 is given so that a previous sample is available at the left edge. We will use two adjacent input samples to construct one output at a time.',
    'Locate the known input and the given starting value.');
  a.statement('given-input', R`x[0..4]=[0,2,4,2,0],\qquad x[-1]=0`, 64, 226, 1144, 58, 31);
  a.text('sequence-label', 'Input sample values', 64, 304, 1144, 38, 27, true);
  const X = n => 220 + (n + 1) * 174;
  const base = 525, scale = 39;
  a.line('input-axis', 176, base, 960, '#9B9B9B', 1.4);
  a.eq('sample-index', 'n', 1163, base + 15, 40, 40, 26);
  values.forEach((v, i) => {
    const n = i - 1, x = X(n), y = base - scale * v;
    if (v) a.shape('stem-' + n, 'rect', x - 1.2, y, 2.4, base - y, '#202020');
    a.shape('dot-' + n, 'ellipse', x - 4.5, y - 4.5, 9, 9, '#202020');
    a.text('value-' + n, String(v), x - 35, y - 40, 70, 32, 27, true, 'center');
    a.text('index-' + n, String(n), x - 35, base + 17, 70, 32, 25, false, 'center');
  });
  a.text('given-history', 'Given', 165, 586, 110, 32, 24, false, 'center', '#777777');
  a.text('first-takeaway', 'Two adjacent input samples produce one output value.', 64, 645, 1144, 42, 31, true);

  page('one-pair', 'One pair, one output', 'At index 2',
    'Select the current sample x[2]=4 and its previous neighbour x[1]=2. An average is halfway between their heights. A click copies these same two heights to output index 2, then brings them together at height 3. The source samples remain visible. After the result holds, the next click records the full arithmetic. The output belongs at index 2, the current index.',
    'See the same two sample heights meet at their average.');
  a.text('halfway-meaning', 'Average: halfway between the two sample heights.', 64, 226, 1144, 43, 29, true);
  await a.demo('pair-to-output', {x:70, y:309, w:1120, h:250, stage:1});
  result('one-pair-answer', R`y[2]=\frac{4+2}{2}=3`, 2, 606);

  page('rule', 'The averaging rule', 'Current and previous',
    'The numerical example uses current value 4 and previous value 2. Replace the specific current index 2 with the integer index n. Then x[n] is current, x[n-1] is previous, and y[n] is the output at that same current index. Add both inputs and divide the sum by 2. Two-point counts the two input samples used for each output.',
    'Read each term of the general averaging rule.');
  a.statement('known-example', R`y[2]=\frac{4+2}{2}=3`, 64, 224, 1144, 70, 29);
  a.eq('current-term', R`x[n]`, 80, 329, 205, 45, 31);
  a.text('current-definition', 'Current input sample at index n', 318, 329, 880, 45, 28);
  a.eq('previous-term', R`x[n-1]`, 80, 394, 205, 45, 31);
  a.text('previous-definition', 'Previous input sample, one index earlier', 318, 394, 880, 45, 28);
  a.reveal(1, () => a.statement('general-rule', rule, 64, 478, 1144, 88, 39));
  a.reveal(2, () => {
    a.text('rule-takeaway', 'Two input samples. One output at the current index n.', 64, 624, 1144, 43, 31, true);
    a.line('rule-emphasis', 64, 679, 1144, '#777777', 1.2);
  });

  page('moving-pair', 'The moving pair', 'One index at a time',
    'Apply the established rule at n=0,1,2,3,4. At n=0 use the supplied previous value x[-1]=0. The outline moves one input index forward for each new output, so successive pairs overlap by one sample. Each output appears only after the selected pair has settled. Earlier outputs stay visible. Only outputs n=0 through n=4 are requested, and no future input is assumed.',
    'Follow the overlapping pair and retain each output.');
  a.statement('moving-rule', rule + R`,\qquad x[-1]=0`, 64, 226, 1144, 71, 30);
  await a.demo('moving-window', {x:70, y:329, w:1120, h:250, stage:1});
  result('all-outputs', R`y[0..4]=[0,1,3,3,1]`, 2, 612);

  page('worked-example', 'Complete worked example', 'All five outputs',
    'This page keeps the problem statement and every numerical substitution visible together. Read previous input, current input, their sum divided by 2, and the resulting output in each row. Notice that x[2]=4 is reused in two overlapping pairs. It produces outputs 3 at both n=2 and n=3. The starting value x[-1]=0 is given. The final vector contains only n=0 through n=4.',
    'Keep a complete reproducible record of every calculation.');
  a.statement('worked-givens', R`x[0..4]=[0,2,4,2,0],\qquad x[-1]=0`, 64, 224, 1144, 55, 29);
  a.comparisonTable('calculation-table', [
    ['n', 'Previous', 'Current', 'Average', 'Output'],
    ['0', '0', '0', '(0 + 0) / 2', '0'],
    ['1', '0', '2', '(2 + 0) / 2', '1'],
    ['2', '2', '4', '(4 + 2) / 2', '3'],
    ['3', '4', '2', '(2 + 4) / 2', '3'],
    ['4', '2', '0', '(0 + 2) / 2', '1']
  ], 64, 300, 1144, 300, {fontSize:28, columnWidths:[95, 225, 225, 359, 240]});
  result('worked-answer', R`y[0..4]=[0,1,3,3,1]`, 0, 621);

  page('takeaway', 'Two-point moving average', 'Takeaway',
    'For each current index n, add x[n] and its previous input x[n-1], then divide by 2 to obtain y[n]. Advance n by one and use the next overlapping pair. Supply a previous input for the first output; here x[-1]=0. In this example, [0,2,4,2,0] becomes [0,1,3,3,1] over the same five indices.',
    'Retain the rule, the one-index movement, and the starting-value condition.');
  a.statement('takeaway-rule', rule, 64, 252, 1144, 91, 41);
  a.text('takeaway-meaning', 'Current + previous, divided by two.', 64, 382, 1144, 44, 32, true);
  a.text('takeaway-move', 'Move forward one index. Use the next overlapping pair.', 64, 449, 1144, 43, 29);
  a.statement('takeaway-start', R`\text{First output: use the given }x[-1]=0.`, 64, 516, 1144, 48, 27);
  result('takeaway-example', R`[0,2,4,2,0]\quad\longmapsto\quad[0,1,3,3,1]`, 0, 615);
}
