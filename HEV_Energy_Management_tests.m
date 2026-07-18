%% REGRESSION TESTS FOR HEV ENERGY MANAGEMENT FIS

projectDir = fileparts(mfilename('fullpath'));
fis = readfis(fullfile(projectDir, 'HEV_Energy_Management.fis'));

% Core operating scenarios: [SoC %, normalized torque demand %, trip km]
inputs = [
     0  60 200;  % Low / Accelerating / Long -> ICE + charging
    50   0   0;  % Medium / Cruising / Short -> Electric
    50   0 200;  % Medium / Cruising / Long -> Hybrid
    50  60 200;  % Medium / Accelerating / Long -> Hybrid
   100   0   0;  % High / Cruising / Short -> Electric
   100   0 200;  % High / Cruising / Long -> Hybrid
   100 100 200;  % High / Heavy / Long -> ICE + charging
    60  60 100;  % Reference scenario -> Hybrid
];

actual = evalfis(fis, inputs);

assert(actual(1) < 0.25, 'Low-SoC long-trip scenario must be ICE-dominant.');
assert(actual(2) > 0.75, 'Medium-SoC short cruise must be electric-dominant.');
assert(actual(3) > 0.35 && actual(3) < 0.65, ...
    'Medium-SoC long cruise must be hybrid.');
assert(actual(4) > 0.35 && actual(4) < 0.65, ...
    'Medium-SoC long acceleration must be hybrid.');
assert(actual(5) > 0.75, 'High-SoC short cruise must be electric-dominant.');
assert(actual(6) > 0.35 && actual(6) < 0.65, ...
    'High-SoC long cruise must conserve energy in hybrid mode.');
assert(actual(7) < 0.25, 'High-load long-trip scenario must be ICE-dominant.');
assert(abs(actual(8) - 0.5) < 0.05, ...
    'Reference scenario must produce an approximately 0.50 electric share.');

% Coverage and range check on a representative operating grid.
[socGrid, torqueGrid, tripGrid] = ndgrid(0:10:100, 0:10:100, 0:20:200);
gridInputs = [socGrid(:), torqueGrid(:), tripGrid(:)];
gridOutputs = evalfis(fis, gridInputs);

assert(all(isfinite(gridOutputs)), 'FIS produced a non-finite output.');
assert(all(gridOutputs >= 0 & gridOutputs <= 1), ...
    'FIS output must stay in the normalized [0,1] range.');

fprintf('All %d scenario and %d grid checks passed.\n', ...
    size(inputs, 1), size(gridInputs, 1));
