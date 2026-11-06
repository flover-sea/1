function c = seawater_sound_speed(T, S, z)
%SEAWATER_SOUND_SPEED Sound speed from the empirical formula in the exercise.
%   c = seawater_sound_speed(T, S, z)
%   T: temperature in degrees Celsius; S: salinity in ppt;
%   z: depth in metres, positive downward; c: sound speed in m/s.
%
%   Inputs may be scalars or arrays with equal or singleton dimensions.
%   For example, T as a column and S as a row produce a T-by-S grid.
%   BSXFUN keeps this implementation compatible with MATLAB releases before
%   implicit array expansion was introduced, and with GNU Octave.
%
%   This function implements the assigned formula without replacing it with
%   a different seawater equation. The exercise does not specify calibration
%   limits or uncertainty. Results compare parameter effects; engineering
%   use requires checking model validity and measured sound-speed profiles.
%   Low-salinity examples need not represent typical open-ocean conditions.

    inputs = {T, S, z};
    names = {'T', 'S', 'z'};
    for k = 1:numel(inputs)
        x = inputs{k};
        if ~isnumeric(x) || ~isreal(x) || isempty(x) || ...
                any(~isfinite(x(:)))
            error('seawater_sound_speed:InvalidInput', ...
                '%s must be a nonempty, finite, real numeric array.', names{k});
        end
    end
    if any(z(:) < 0)
        error('seawater_sound_speed:NegativeDepth', ...
            'Depth z must be nonnegative (metres, positive downward).');
    end

    % Convert integer inputs as well as floating-point inputs consistently.
    T = double(T);
    S = double(S);
    z = double(z);
    temperature_term = 1449.2 + 4.6 .* T - 0.055 .* T.^2 ...
        + 0.00029 .* T.^3;
    salinity_term = bsxfun(@times, 1.34 - 0.01 .* T, S - 35);
    c = bsxfun(@plus, temperature_term, salinity_term);
    c = bsxfun(@plus, c, 0.016 .* z);
end
