import { useEffect } from 'react';
import { Cpu, Sparkles } from 'lucide-react';
import { useAppStore } from '../lib/store';

/**
 * Selector de motor: IA local (Ollama) o Claude Code (tu suscripción, modo headless).
 *
 * Cambia el modelo seleccionado de la app. Recuerda el último modelo usado en
 * cada motor para que pasar de uno a otro sea un solo clic.
 */

const CC_PREFIX = 'claudecode/';
const LS_LOCAL = 'oj-engine-last-local';
const LS_CLAUDE = 'oj-engine-last-claude';

const CLAUDE_MODELS: Array<{ id: string; label: string; hint: string }> = [
  { id: 'claudecode/sonnet', label: 'Sonnet', hint: 'Equilibrado' },
  { id: 'claudecode/opus', label: 'Opus', hint: 'Máxima calidad' },
  { id: 'claudecode/haiku', label: 'Haiku', hint: 'Más rápido' },
];

const read = (k: string) => {
  try { return localStorage.getItem(k) || ''; } catch { return ''; }
};
const write = (k: string, v: string) => {
  try { localStorage.setItem(k, v); } catch { /* sin almacenamiento */ }
};

export function EngineSwitch() {
  const models = useAppStore((s) => s.models);
  const selectedModel = useAppStore((s) => s.selectedModel);
  const setSelectedModel = useAppStore((s) => s.setSelectedModel);

  const ids = models.map((m) => m.id);
  const claudeAvailable = ids.some((id) => id.startsWith(CC_PREFIX));
  const localIds = ids.filter((id) => !id.startsWith(CC_PREFIX));
  const isClaude = selectedModel.startsWith(CC_PREFIX);

  // Recordar el último modelo usado en cada motor.
  useEffect(() => {
    if (!selectedModel) return;
    write(isClaude ? LS_CLAUDE : LS_LOCAL, selectedModel);
  }, [selectedModel, isClaude]);

  if (!claudeAvailable) return null;

  const pickLocal = () => {
    if (!isClaude) return;
    const last = read(LS_LOCAL);
    setSelectedModel(localIds.includes(last) ? last : localIds[0] ?? '');
  };
  const pickClaude = () => {
    if (isClaude) return;
    const last = read(LS_CLAUDE);
    setSelectedModel(ids.includes(last) ? last : 'claudecode/sonnet');
  };

  return (
    <div className="oj-engine mx-3 mb-2" data-no-translate>
      <div className="oj-engine-label">Motor de IA</div>
      <div className="oj-engine-seg" role="radiogroup" aria-label="Motor de IA">
        <button
          type="button"
          role="radio"
          aria-checked={!isClaude}
          className={`oj-engine-opt ${!isClaude ? 'is-on is-local' : ''}`}
          onClick={pickLocal}
          disabled={localIds.length === 0}
          title="Modelo local en tu equipo (privado, sin conexión)"
        >
          <Cpu size={14} />
          <span>Local</span>
        </button>
        <button
          type="button"
          role="radio"
          aria-checked={isClaude}
          className={`oj-engine-opt ${isClaude ? 'is-on is-claude' : ''}`}
          onClick={pickClaude}
          title="Claude Code con tu suscripción (los mensajes se envían a Anthropic)"
        >
          <Sparkles size={14} />
          <span>Claude</span>
        </button>
        <span className={`oj-engine-thumb ${isClaude ? 'right' : ''}`} aria-hidden="true" />
      </div>

      {isClaude && (
        <>
          <div className="oj-engine-models">
            {CLAUDE_MODELS.map((m) => (
              <button
                key={m.id}
                type="button"
                className={`oj-engine-chip ${selectedModel === m.id ? 'is-on' : ''}`}
                onClick={() => setSelectedModel(m.id)}
                title={m.hint}
              >
                {m.label}
              </button>
            ))}
          </div>
          <div className="oj-engine-note">
            Usa tu suscripción de Claude Code · los mensajes salen de tu equipo
          </div>
        </>
      )}
    </div>
  );
}
