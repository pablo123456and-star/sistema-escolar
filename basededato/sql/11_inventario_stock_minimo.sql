-- =====================================================================
-- 11 - INVENTARIO: STOCK MINIMO  -  SISTEMA ESCUELA MODELO
-- Requiere: 01 a 07
-- =====================================================================
-- Cada bien puede tener un stock minimo. El backend (CU26) marca el bien
-- como "stock bajo" cuando su cantidad llega a ese minimo, y "sin stock"
-- cuando llega a 0. Un minimo de 0 significa que el bien no tiene alerta.
-- La regla la aplica el backend; la BD solo guarda el dato y evita
-- valores negativos.
-- Se puede ejecutar mas de una vez sin error.
-- =====================================================================

BEGIN;

ALTER TABLE inventario
    ADD COLUMN IF NOT EXISTS stock_minimo INTEGER NOT NULL DEFAULT 0;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'inventario_stock_minimo_check') THEN
        ALTER TABLE inventario
            ADD CONSTRAINT inventario_stock_minimo_check CHECK (stock_minimo >= 0);
    END IF;
END $$;

COMMENT ON COLUMN inventario.stock_minimo IS
    'Cantidad minima deseada del bien (0 = sin alerta). El CU26 avisa "stock bajo" al llegar a este valor.';

COMMIT;
