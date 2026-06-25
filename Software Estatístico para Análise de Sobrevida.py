#!/usr/bin/env python
# coding: utf-8

# In[3]:


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import customtkinter as ctk
from tkinter import filedialog, messagebox
import matplotlib.backends.backend_tkagg as tkagg
from lifelines import KaplanMeierFitter, CoxPHFitter
from lifelines.utils import restricted_mean_survival_time
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.nonparametric.smoothers_lowess import lowess
import os
from lifelines.statistics import logrank_test


class SurvivalApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Análise de Sobrevida (Survival Analysis) - By Eduardo Borba Neves")
        self.geometry("1200x700")
        self.df = None
        self.checkboxes = {}
        self.figs = []
        self.custom_references = {} # Dicionário para armazenar referências escolhidas pelo usuário
        self.setup_ui()
        self.protocol("WM_DELETE_WINDOW", self.safe_exit)


    def setup_ui(self):
        # 1. Sidebar (Mantida à esquerda para configurações de variáveis)
        self.sidebar = ctk.CTkScrollableFrame(self, width=320, label_text="Configurações da Análise")
        self.sidebar.pack(side="left", fill="y", padx=10, pady=10)

        ctk.CTkButton(self.sidebar, text="1. Carregar Excel", command=self.load_file, fg_color="#34495e").pack(pady=10, padx=10, fill="x")

        self.lbl_ev = ctk.CTkLabel(self.sidebar, text="Variável de Evento:", font=("Roboto", 12, "bold"))
        self.lbl_ev.pack(pady=(10,0)); self.cb_evento = ctk.CTkComboBox(self.sidebar, command=self.refresh_ui); self.cb_evento.pack(pady=5)
        
        self.lbl_ni = ctk.CTkLabel(self.sidebar, text="Nível do Evento Positivo:", font=("Roboto", 12, "bold"))
        self.lbl_ni.pack(pady=(10,0)); self.cb_nivel = ctk.CTkComboBox(self.sidebar); self.cb_nivel.pack(pady=5)
        
        self.lbl_te = ctk.CTkLabel(self.sidebar, text="Tempo até Evento:", font=("Roboto", 12, "bold"))
        self.lbl_te.pack(pady=(10,0)); self.cb_tempo = ctk.CTkComboBox(self.sidebar, command=self.refresh_ui); self.cb_tempo.pack(pady=5)
        
        self.lbl_gr = ctk.CTkLabel(self.sidebar, text="Separar Grupos Por:", font=("Roboto", 12, "bold"))
        self.lbl_gr.pack(pady=(10,0)); self.cb_grupo = ctk.CTkComboBox(self.sidebar, command=self.refresh_ui); self.cb_grupo.pack(pady=5)

        self.lbl_ctrl = ctk.CTkLabel(self.sidebar, text="Fatores de Controle (Ajuste):", font=("Roboto", 12, "bold"))
        self.lbl_ctrl.pack(pady=(20, 5))
        self.frame_checks = ctk.CTkFrame(self.sidebar)
        self.frame_checks.pack(fill="x", padx=5, pady=5)

        # 2. Contêiner Principal à Direita
        self.right_container = ctk.CTkFrame(self, fg_color="transparent")
        self.right_container.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        # 3. NOVO: Frame de Botões (Topo da área de resultados)
        self.top_button_frame = ctk.CTkFrame(self.right_container)
        self.top_button_frame.pack(side="top", fill="x", pady=(0, 10))

        # Botões organizados horizontalmente
        self.btn_run = ctk.CTkButton(self.top_button_frame, text="Rodar Análise Completa", 
                                     fg_color="#27ae60", hover_color="#2ecc71", command=self.run_analysis)
        self.btn_run.pack(side="left", expand=True, fill="x", padx=5, pady=10)
        
        self.btn_export = ctk.CTkButton(self.top_button_frame, text="Exportar Resultados", 
                                        fg_color="#f39c12", command=self.export_results)
        self.btn_export.pack(side="left", expand=True, fill="x", padx=5, pady=10)
        
        self.btn_exit = ctk.CTkButton(self.top_button_frame, text="Fechar e Sair", 
                                      fg_color="#c0392b", hover_color="#e74c3c", command=self.safe_exit)
        self.btn_exit.pack(side="left", expand=True, fill="x", padx=5, pady=10)

        # 4. Painel de Resultados (Abaixo dos botões)
        self.result_frame = ctk.CTkScrollableFrame(self.right_container, label_text="Análise Avançada de Sobrevida")
        self.result_frame.pack(side="bottom", fill="both", expand=True)

        # NOVO: Frame para Controle de Referências
        self.ref_control_frame = ctk.CTkFrame(self.result_frame)
        self.ref_control_frame.pack(fill="x", padx=10, pady=(5, 10))
        
        ctk.CTkLabel(self.ref_control_frame, text="Ajustar Referência:", font=("Roboto", 11, "bold")).pack(side="left", padx=5)
        
        self.cb_ref_var = ctk.CTkComboBox(self.ref_control_frame, width=150, command=self.update_ref_levels_cb)
        self.cb_ref_var.pack(side="left", padx=5)
        
        ctk.CTkLabel(self.ref_control_frame, text="Para:").pack(side="left", padx=2)
        
        self.cb_ref_level = ctk.CTkComboBox(self.ref_control_frame, width=150)
        self.cb_ref_level.pack(side="left", padx=5)
        
        self.btn_update_ref = ctk.CTkButton(self.ref_control_frame, text="Atualizar Referência", 
                                            width=120, fg_color="#2980b9", command=self.apply_custom_reference)
        self.btn_update_ref.pack(side="left", padx=10)

        self.text_result = ctk.CTkTextbox(self.result_frame, height=500, font=("Consolas", 11))
        self.text_result.pack(fill="x", pady=10)
        
    

    def load_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
        if file_path:
            self.df = pd.read_excel(file_path)
            cols = list(self.df.columns)
            self.cb_evento.configure(values=cols); self.cb_tempo.configure(values=cols); self.cb_grupo.configure(values=cols)
            self.refresh_ui()

    def refresh_ui(self, _=None):
        if self.df is None: return
        ev = self.cb_evento.get()
        if ev in self.df.columns:
            self.cb_nivel.configure(values=[str(l) for l in self.df[ev].unique()])
        
        # Atualiza checkboxes excluindo os combos
        for w in self.frame_checks.winfo_children(): w.destroy()
        self.checkboxes = {}
        selecionados = [self.cb_evento.get(), self.cb_tempo.get(), self.cb_grupo.get()]
        for col in self.df.columns:
            if col not in selecionados:
                var = ctk.BooleanVar()
                ctk.CTkCheckBox(self.frame_checks, text=col, variable=var).pack(anchor="w", padx=10, pady=2)
                self.checkboxes[col] = var
    
    

    def run_analysis(self):
        if self.df is None: 
            messagebox.showwarning("Aviso", "Por favor, carregue um arquivo primeiro.")
            return
        
        try:
            # 1. FECHA TODAS AS FIGURAS ANTERIORES PARA LIBERAR MEMÓRIA
            plt.close('all') 
            
            self.figs = []
            for child in self.result_frame.winfo_children():
                if child != self.text_result and child != self.ref_control_frame:
                    child.destroy()
            # Força o coletor de lixo para garantir estabilidade
            import gc
            gc.collect() 
            
            ev, t, grp, pos = self.cb_evento.get(), self.cb_tempo.get(), self.cb_grupo.get(), self.cb_nivel.get()
            selected_covars = [col for col, var in self.checkboxes.items() if var.get()]
            
            cols_to_use = [ev, t, grp] + selected_covars
            data = self.df[cols_to_use].copy().dropna()
            data['event_binary'] = (data[ev].astype(str) == pos).astype(int)
            
            # --- FUNÇÕES AUXILIARES ---
            def is_categorical_var(col):
                if col == grp: return True
                s = data[col]
                return (pd.api.types.is_object_dtype(s) or 
                        isinstance(s.dtype, pd.CategoricalDtype) or 
                        pd.api.types.is_bool_dtype(s) or 
                        s.nunique() <= 5)

            analysis_vars = [grp] + selected_covars
            self.cb_ref_var.configure(values=[v for v in analysis_vars if v in data.columns and is_categorical_var(v)])

            categorical_vars = [v for v in analysis_vars if v in data.columns and is_categorical_var(v)]
            continuous_vars = [v for v in analysis_vars if v in data.columns and v not in categorical_vars]

            cat_info = {}
            for var in categorical_vars:
                tmp = data[[var]].copy(); tmp[var] = tmp[var].astype(str)
                all_cols = pd.get_dummies(tmp, columns=[var], drop_first=False).columns.tolist()
                prefix = f"{var}_"
                levels = [str(col).replace(prefix, "", 1) for col in all_cols]
                ref_level = self.custom_references.get(var, levels[0] if levels else None)
                if ref_level not in levels and levels: ref_level = levels[0]
                cat_info[var] = {
                    'levels': levels, 'all_cols': all_cols, 'reference_level': ref_level,
                    'level_to_col': {str(col).replace(prefix, "", 1): col for col in all_cols}
                }

            def build_model_matrix(base_df, variables):
                cols = [t, 'event_binary'] + variables
                model_df = base_df[cols].copy()
                final_cols = [t, 'event_binary']
                for var in variables:
                    if var in categorical_vars:
                        ref = cat_info[var]['reference_level']
                        ordered = [ref] + [l for l in cat_info[var]['levels'] if l != ref]
                        model_df[var] = pd.Categorical(model_df[var].astype(str), categories=ordered)
                        dummies = pd.get_dummies(model_df[[var]], prefix=var, drop_first=True)
                        final_cols.extend(dummies.columns.tolist())
                        model_df = pd.concat([model_df, dummies], axis=1)
                    else: final_cols.append(var)
                return model_df[final_cols].astype(float)

            df_model = build_model_matrix(data, analysis_vars)
            cph = CoxPHFitter(); cph.fit(df_model, duration_col=t, event_col='event_binary')
            summ = cph.summary

            def format_float(v, d=3): return "NA" if pd.isna(v) else f"{v:.{d}f}"
            def format_p(v): return "NA" if pd.isna(v) else ("<0.001" if v < 0.001 else f"{v:.3f}")
            def format_ci(l, h): return "NA" if pd.isna(l) or pd.isna(h) else f"{l:.3f}–{h:.3f}"
            def extract_hr(s_df, term):
                if term not in s_df.index: return np.nan, np.nan, np.nan, np.nan
                r = s_df.loc[term]
                return r.get('exp(coef)', np.nan), r.get('exp(coef) lower 95%', np.nan), r.get('exp(coef) upper 95%', np.nan), r.get('p', np.nan)

            univ_summaries = {}
            for var in analysis_vars:
                try:
                    df_u = build_model_matrix(data, [var])
                    c_u = CoxPHFitter(); c_u.fit(df_u, duration_col=t, event_col='event_binary')
                    univ_summaries[var] = c_u.summary
                except: univ_summaries[var] = pd.DataFrame()

            hr_rows, forest_rows = [], []
            for var in analysis_vars:
                if var not in data.columns: continue
                u_s = univ_summaries.get(var, pd.DataFrame())
                if var in categorical_vars:
                    ref_l = cat_info[var]['reference_level']
                    for level in cat_info[var]['levels']:
                        term = cat_info[var]['level_to_col'].get(level); is_ref = (level == ref_l)
                        hr_u, lo_u, hi_u, p_u = (1.0, 1.0, 1.0, np.nan) if is_ref else extract_hr(u_s, term)
                        hr_m, lo_m, hi_m, p_m = (1.0, 1.0, 1.0, np.nan) if is_ref else extract_hr(summ, term)
                        hr_rows.append({'Variável': var, 'Categoria': level, 'Referência': 'Sim' if is_ref else 'Não',
                                        'HR univariável': format_float(hr_u), 'IC95% univariável': 'Referência' if is_ref else format_ci(lo_u, hi_u),
                                        'p univariável': 'Referência' if is_ref else format_p(p_u),
                                        'HR multivariável': format_float(hr_m), 'IC95% multivariável': 'Referência' if is_ref else format_ci(lo_m, hi_m),
                                        'p multivariável': 'Referência' if is_ref else format_p(p_m)})
                        forest_rows.append({'label': f"{var}: {level}" + (" (ref.)" if is_ref else ""), 'hr': hr_m, 'lower': lo_m, 'upper': hi_m, 'is_reference': is_ref})
                else:
                    hr_u, lo_u, hi_u, p_u = extract_hr(u_s, var); hr_m, lo_m, hi_m, p_m = extract_hr(summ, var)
                    hr_rows.append({'Variável': var, 'Categoria': 'Contínua', 'Referência': 'Não',
                                    'HR univariável': format_float(hr_u), 'IC95% univariável': format_ci(lo_u, hi_u), 'p univariável': format_p(p_u),
                                    'HR multivariável': format_float(hr_m), 'IC95% multivariável': format_ci(lo_m, hi_m), 'p multivariável': format_p(p_m)})
                    forest_rows.append({'label': f"{var} (cont.)", 'hr': hr_m, 'lower': lo_m, 'upper': hi_m, 'is_reference': False})

            hr_results_df = pd.DataFrame(hr_rows); forest_df = pd.DataFrame(forest_rows)

            # --- RELATÓRIO ---
            output = "="*50 + "\n      RELATÓRIO DE ANÁLISE DE SOBREVIDA\n" + "="*50 + "\n\n"
            groups = data[grp].unique(); p_logrank = None
            if len(groups) == 2:
                g1, g2 = groups[0], groups[1]
                res_lr = logrank_test(data[t][data[grp] == g1], data[t][data[grp] == g2], data['event_binary'][data[grp] == g1], data['event_binary'][data[grp] == g2])
                p_logrank = res_lr.p_value
                output += f"--- COMPARAÇÃO DE GRUPOS (LOG-RANK) ---\n• P-valor Log-rank: {p_logrank:.4f}\n"
                output += f"  -> Interpretação: {'Diferença estatisticamente significativa' if p_logrank < 0.05 else 'Não há diferença significativa'} entre as curvas de sobrevida brutas.\n\n"

            t_max = data[t].max(); time_grid = np.linspace(0.1, t_max, 50)
            surv_matrix = cph.predict_survival_function(df_model, times=time_grid)
            bs_list = [np.mean(((data[t] > tp).astype(int) - surv_matrix.loc[tp])**2) for tp in time_grid]
            ibs = np.mean(bs_list)
            output += f"--- ACURÁCIA GLOBAL (IBS) ---\n• IBS Final: {ibs:.4f}\n"
            if ibs <= 0.10: interp_ibs = "Excelente desempenho global."
            elif ibs <= 0.20: interp_ibs = "Bom desempenho global."
            else: interp_ibs = "Desempenho moderado/baixo."
            output += f"  -> Interpretação: {interp_ibs}\n\n"

            n_eventos = data['event_binary'].sum(); epv = n_eventos / len(cph.params_) if len(cph.params_) > 0 else 0
            output += f"--- DESEMPENHO E ADEQUAÇÃO ---\n• C-index: {cph.concordance_index_:.3f}\n"
            if cph.concordance_index_ >= 0.7: output += "  -> Interpretação: Bom poder discriminatório.\n"
            else: output += "  -> Interpretação: Poder discriminatório moderado/baixo.\n"
            output += f"• AIC: {cph.AIC_partial_:.2f}\n• Eventos: {n_eventos} | EPV: {epv:.2f}\n"
            if epv < 10: output += f"  -> ALERTA: EPV baixo ({epv:.2f}). Risco de superajuste.\n"
            output += "\n--- MODELO DE COX: HR POR CATEGORIA ---\n" + hr_results_df.to_string(index=False) + "\n\n"

            output += "--- COLINEARIDADE (VIF) ---\n"
            X_vif = df_model.drop(columns=[t, 'event_binary'])
            if X_vif.shape[1] > 1:
                for i, col_v in enumerate(X_vif.columns):
                    v_val = variance_inflation_factor(X_vif.values, i)
                    output += f"{col_v}: {v_val:.2f} {'(ALTA!)' if v_val > 5 else '(OK)'}\n"
            output += "\n--- TESTE DE SCHOENFELD (PH ASSUMPTION) ---\n"
            try:
                from lifelines.statistics import proportional_hazard_test
                res_sch = proportional_hazard_test(cph, df_model, time_transform='rank')
                output += res_sch.summary.to_string() + "\n"
                if res_sch.p_value.min() < 0.05: output += "-> ATENÇÃO: Violação detectada na premissa de riscos proporcionais.\n"
                else: output += "-> Interpretação: Premissa atendida para todas as variáveis.\n"
            except: output += "Teste de Schoenfeld indisponível.\n"

            output += "\n\n" + "="*40 + "\nCOMO CITAR ESTE SOFTWARE:\n" + "="*40 + "\n"
            # --- Seção de Citações Multiformato ---
            citacoes = (
                    "ABNT:\n"
                    "NEVES, Eduardo Borba. Software Estatístico para Análise de Sobrevida."
                    "Versão 1.0. [S.l.]: 2026. Software.\n\n"
                    
                    "APA:\n"
                    "Neves, E. B. (2026). Software Estatístico para Análise de Sobrevida."
                    "(Versão 1.0) [Software].\n\n"
                    
                    "IEEE:\n"
                    "E. B. Neves, \"Software Estatístico para Análise de Sobrevida,\" "
                    "ver. 1.0, 2026. [Software].\n\n"
                    
                    "VANCOUVER:\n"
                    "Neves EB. Software Estatístico para Análise de Sobrevida [Software]. "
                    "Versão 1.0. [S.l.]: 2026.\n"
                )

            output += citacoes
            #output += "NEVES, Eduardo Borba. Software Estatístico para Análise de Sobrevida. [Software]. 2026.\n"

            self.text_result.delete("1.0", "end"); self.text_result.insert("end", output)

            # Limpa a lista de figuras antes de começar
            self.figs = [] 

            # --- FIGURA 1: SOBREVIDA ---
            fig1, (ax_km, ax_adj) = plt.subplots(1, 2, figsize=(14, 6))
            for name, g_df in data.groupby(grp):
                KaplanMeierFitter().fit(g_df[t], g_df['event_binary'], label=f"{grp} ({name})").plot_survival_function(ax=ax_km)
            ax_km.set_title("Kaplan-Meier (Brutas)"); ax_km.set_xlabel("Tempo")

            base_prof = df_model.drop(columns=[t, 'event_binary']).mean().to_frame().T
            if grp in cat_info:
                for level in cat_info[grp]['levels']:
                    prof = base_prof.copy()
                    for c in cat_info[grp]['all_cols']: 
                        if c in prof.columns: prof[c] = 0
                    term = cat_info[grp]['level_to_col'].get(level)
                    if term in prof.columns: prof[term] = 1
                    surv_adj = cph.predict_survival_function(prof)
                    ax_adj.plot(surv_adj.index, surv_adj.iloc[:, 0], label=f"Ajustada: {grp} ({level})")
            ax_adj.set_title("Sobrevida Ajustada"); ax_adj.legend(fontsize='small')
            self.figs.append(fig1)

            # --- FIGURA 2: FOREST PLOT ---
            plot_df = forest_df.dropna(subset=['hr']).iloc[::-1].reset_index(drop=True)
            fig2, ax_f = plt.subplots(figsize=(10, max(6, 0.4*len(plot_df)+2)))
            for i, row in plot_df.iterrows():
                if row['is_reference']:
                    ax_f.scatter(1.0, i, color='black', marker='s', s=50, zorder=4)
                    ax_f.text(1.0, i, ' (ref.)', va='center', fontweight='bold', fontsize=8)
                else:
                    ax_f.errorbar(row['hr'], i, xerr=[[max(row['hr']-row['lower'],0)], [max(row['upper']-row['hr'],0)]], 
                                  fmt='o', color='#1f77b4', ecolor='#1f77b4', capsize=3)
            ax_f.set_yticks(np.arange(len(plot_df))); ax_f.set_yticklabels(plot_df['label'])
            ax_f.axvline(1, color='red', linestyle='--'); ax_f.set_xscale('log')
            ax_f.set_title("Forest Plot: HR Ajustados")
            plt.tight_layout(); self.figs.append(fig2)

            # --- FIGURA 3: RESÍDUOS DE SCHOENFELD (Altura Ajustada) ---
            residuals = cph.compute_residuals(df_model, 'schoenfeld').sort_index()
            n_res = len(residuals.columns)
            
            # Altura alterada de 4 * n_res para 2 * n_res
            fig3, axes = plt.subplots(n_res, 1, figsize=(10, 2 * n_res), sharex=True) 
            
            if n_res == 1: axes = [axes]
            for i, col in enumerate(residuals.columns):
                axes[i].scatter(residuals.index, residuals[col], alpha=0.3, s=20, color='gray')
                try:
                    smooth = lowess(residuals[col], residuals.index)
                    axes[i].plot(smooth[:, 0], smooth[:, 1], color='red', lw=2)
                except: pass
                axes[i].axhline(0, color='black', linestyle='--')
                axes[i].set_ylabel(f"Resíduo: {col}", fontsize=9)
            fig3.suptitle("Diagnóstico de Proporcionalidade (Schoenfeld)", fontsize=14)
            plt.tight_layout(rect=[0, 0.03, 1, 0.97]); self.figs.append(fig3)

            # --- EXIBIÇÃO E ATUALIZAÇÃO DA INTERFACE ---
            for f in self.figs:
                canvas = tkagg.FigureCanvasTkAgg(f, master=self.result_frame)
                canvas.draw()
                canvas.get_tk_widget().pack(fill="x", pady=20)
            
            # Comando crucial para forçar a renderização dos widgets no frame
            self.update_idletasks()
        except Exception as e: messagebox.showerror("Erro", f"Falha na análise: {e}")

    def export_results(self):
        if not self.figs: return
        path = filedialog.asksaveasfilename(defaultextension=".txt")
        if path:
            with open(path, "w") as f: f.write(self.text_result.get("1.0", "end"))
            base = os.path.splitext(path)[0]
            for i, fig in enumerate(self.figs): fig.savefig(f"{base}_fig_{i}.png", dpi=300)
            messagebox.showinfo("Sucesso", "Resultados exportados!")

    def safe_exit(self):
        plt.close('all'); self.quit(); self.destroy()


    def update_ref_levels_cb(self, var_name):
        if self.df is None or var_name not in self.df.columns: return
        levels = [str(l) for l in sorted(self.df[var_name].dropna().unique())]
        self.cb_ref_level.configure(values=levels)
        if levels: self.cb_ref_level.set(levels[0])

    def apply_custom_reference(self):
        var = self.cb_ref_var.get()
        level = self.cb_ref_level.get()
        if var and level:
            self.custom_references[var] = level
            self.run_analysis()


if __name__ == "__main__":
    SurvivalApp().mainloop()


# In[ ]:




