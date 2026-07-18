%% SMART ENERGY MANAGEMENT FUZZY LOGIC SYSTEM (HEV)

projectDir = fileparts(mfilename('fullpath'));

% Create FIS
fis = mamfis('Name', 'HEV_Energy_Management');

%% (INPUTS)
% Input 1: Battery SoC
fis = addInput(fis, [0 100], 'Name', 'SoC');
fis = addMF(fis, 'SoC', 'trimf', [0 0 40], 'Name', 'Low');
fis = addMF(fis, 'SoC', 'trimf', [30 50 70], 'Name', 'Medium');
fis = addMF(fis, 'SoC', 'trimf', [60 100 100], 'Name', 'High');

% Input 2: Normalized Torque Demand (%)
fis = addInput(fis, [0 100], 'Name', 'Torque');
fis = addMF(fis, 'Torque', 'trimf', [0 0 40], 'Name', 'Cruising');
fis = addMF(fis, 'Torque', 'trimf', [30 60 80], 'Name', 'Accelerating');
fis = addMF(fis, 'Torque', 'trimf', [70 100 100], 'Name', 'Heavy_Load');

% Input 3: Estimated Trip Distance (km)
fis = addInput(fis, [0 200], 'Name', 'Trip_Distance');
fis = addMF(fis, 'Trip_Distance', 'trimf', [0 0 30], 'Name', 'Short');
fis = addMF(fis, 'Trip_Distance', 'trimf', [20 60 100], 'Name', 'Medium');
fis = addMF(fis, 'Trip_Distance', 'trimf', [80 200 200], 'Name', 'Long');

%% (OUTPUT)
% Output: Electric-motor contribution ratio.
% 0 means ICE-dominant operation and 1 means electric-dominant operation.
fis = addOutput(fis, [0 1], 'Name', 'Power_Split');
fis = addMF(fis, 'Power_Split', 'trimf', [0.6 1 1], 'Name', 'Electric');     % Output=1
fis = addMF(fis, 'Power_Split', 'trimf', [0.3 0.5 0.7], 'Name', 'Hybrid');   % Output=2
fis = addMF(fis, 'Power_Split', 'trimf', [0 0 0.4], 'Name', 'ICE_Charge');   % Output=3

%% (RULES) - 27 COMBINATIONS

rules = [
    % --- SoC LOW ---
    1 1 1 3 1 1; % Low, Cruising, Short -> ICE_Charge
    1 1 2 3 1 1; % Low, Cruising, Med   -> ICE_Charge
    1 1 3 3 1 1; % Low, Cruising, Long  -> ICE_Charge
    1 2 1 3 1 1; % Low, Accel, Short    -> ICE_Charge
    1 2 2 3 1 1; % Low, Accel, Med      -> ICE_Charge
    1 2 3 3 1 1; % Low, Accel, Long     -> ICE_Charge
    1 3 1 3 1 1; % Low, Heavy, Short    -> ICE_Charge
    1 3 2 3 1 1; % Low, Heavy, Med      -> ICE_Charge
    1 3 3 3 1 1; % Low, Heavy, Long     -> ICE_Charge

    % --- SoC MEDIUM ---
    2 1 1 1 1 1; % Med, Cruising, Short -> Electric
    2 1 2 1 1 1; % Med, Cruising, Med   -> Electric
    2 1 3 2 1 1; % Med, Cruising, Long  -> Hybrid (battery conservation)
    2 2 1 2 1 1; % Med, Accel, Short    -> Hybrid
    2 2 2 2 1 1; % Med, Accel, Med      -> Hybrid
    2 2 3 2 1 1; % Med, Accel, Long     -> Hybrid
    2 3 1 2 1 1; % Med, Heavy, Short    -> Hybrid
    2 3 2 3 1 1; % Med, Heavy, Med      -> ICE_Charge
    2 3 3 3 1 1; % Med, Heavy, Long     -> ICE_Charge

    % --- SoC HIGH ---
    3 1 1 1 1 1; % High, Cruising, Short -> Electric
    3 1 2 1 1 1; % High, Cruising, Med   -> Electric
    3 1 3 2 1 1; % High, Cruising, Long  -> Hybrid (battery conservation)
    3 2 1 1 1 1; % High, Accel, Short    -> Electric
    3 2 2 2 1 1; % High, Accel, Med      -> Hybrid
    3 2 3 2 1 1; % High, Accel, Long     -> Hybrid
    3 3 1 2 1 1; % High, Heavy, Short    -> Hybrid
    3 3 2 2 1 1; % High, Heavy, Med      -> Hybrid
    3 3 3 3 1 1; % High, Heavy, Long     -> ICE_Charge
];

fis = addRule(fis, rules);

%% (REPRODUCIBLE SCENARIO RESULTS)

scenarioInputs = [
    10  60 180;  % Low SoC, accelerating, long trip
    50  10 180;  % Medium SoC, cruising, long trip
    50  60 180;  % Medium SoC, accelerating, long trip
    90  10  10;  % High SoC, cruising, short trip
    90  90 180;  % High SoC, heavy load, long trip
    60  60 100;  % Reported reference scenario
];

powerSplit = evalfis(fis, scenarioInputs);
scenarioResults = array2table([scenarioInputs powerSplit], ...
    'VariableNames', {'SoC_percent', 'TorqueDemand_percent', ...
    'TripDistance_km', 'ElectricPowerShare'});
disp(scenarioResults);

writeFIS(fis, fullfile(projectDir, 'HEV_Energy_Management.fis'));

% Open the current Fuzzy Logic Designer only in an interactive desktop session.
if usejava('desktop')
    fuzzyLogicDesigner(fis);
end
