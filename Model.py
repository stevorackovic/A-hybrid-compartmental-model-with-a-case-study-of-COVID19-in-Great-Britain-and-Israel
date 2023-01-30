"""
Created on Dec 2021

@author: BIGMATH
"""

import numpy as np
from networks import create_networks
from seird import seird_iteration

def get_networks(M,reg_sizes,kids_perc,k=4):
    L_hard_lock_reg= [[] for m in range(M)]
    L_s_reg        = [[] for m in range(M)]
    L_m_reg        = [[] for m in range(M)]
    L_l_reg        = [[] for m in range(M)]
    R_s_reg        = [[] for m in range(M)]
    R_m_reg        = [[] for m in range(M)]
    R_l_reg        = [[] for m in range(M)]
    kids_all_reg   = [[] for m in range(M)]    
    for m in range(M):
        L_hard_lock_reg[m], L_s_reg[m],L_m_reg[m],L_l_reg[m], R_s_reg[m], R_m_reg[m], R_l_reg[m], kids_all_reg[m] = create_networks(reg_sizes[m],kids_perc,k=k)
    return L_hard_lock_reg, L_s_reg, L_m_reg,L_l_reg, R_s_reg, R_m_reg, R_l_reg, kids_all_reg

def run_model(M, reg_sizes, p_e_vector, p_i, p_r, p_h_d, p_h_r, p_asy, p_sy_h, p_international, v_eff, tests, testing_policy, vaccines,
              p_s, contact_tracing, repetition_number, num_days, flag_wp_sch, flag_hard_lock, flag_international,
              p_sy_t, day_init,n_I_init,n_E_init,kids_perc,k=4,probs_ct=[.65,.8],mix_perc=[0,.10]):
    '''
    Paramerets:
                      M - int; number of regions
              reg_sizes - list of integers; sizes of each of M regions
             p_e_vector - list of scalars; values of p_e for each day in simulation, 
                          where p_e is a probability of catching a virus from an 
                          infected contact
                  tests - list of integers; number of tests performed at each day 
                          of the simulation
         testing_policy - list of strings; a testing policy performed over each day 
                          of the simulation
               vaccines - list of integers; number of vaccines given at each day 
                          of the simulation
        contact_tracing - list of integers; flags representing the contact tracing 
                          policy for each day of the simulation
      repetition_number - int; the model is executed repetition_number, to show 
                          the variance of the results
               num_days - int; the lenght of simulation in days
            flag_wp_sch -
         flag_hard_lock -
               day_init - int; a day in simulation when we introduce infected and 
                          exposed cases for the first time
               n_I_init - int; number of infected nodes introduced at a day day_init
               n_E_init - int; number of exposed nodes introduced at a day day_init
               probs_ct - list; a percentage of contacts quaranteened when a contact 
                          tracing policy is '1', and when it is '2', respectively
    The rest of the parameters are described in function 'seird_iteration()'.
    
    '''
    L_hard_lock_reg, L_s_reg, L_m_reg,L_l_reg, R_s_reg, R_m_reg, R_l_reg, kids_all_reg = get_networks(M,reg_sizes,kids_perc,k=k)

    total_size = np.sum(reg_sizes)
    # Initialize empty matrices - here we shall add results for each repetition i.e. simulation
    dH_mtx, dE_mtx, dR_mtx, dD_mtx, dAsy_mtx, dSy_mtx, cH_mtx, NC_mtx = np.zeros((repetition_number, num_days)), np.zeros(
            (repetition_number, num_days)), np.zeros((repetition_number, num_days)), np.zeros(
            (repetition_number, num_days)), np.zeros((repetition_number, num_days)), np.zeros(
            (repetition_number, num_days)), np.zeros((repetition_number, num_days)), np.zeros((repetition_number,num_days))

    for repetition in range(repetition_number):

        print('Run', repetition + 1, 'of', repetition_number)
        # Lists where we add new hospitalized, exposed, recovered... for each region separatelly:
        Det, H_reg, E_reg, R_reg, D_reg, Asy_reg, Sy_reg, Q_Asy_reg, Q_Sy_reg, V_reg, Q_S_reg, Q_E_reg = [
            [[] for m in range(M)] for i in range(12)]
        # Lists where we add new hospitalized, exposed, recovered... for a whole graph (all the regions):
        dH_list, dE_list, dR_list, dD_list, dAsy_list, dSy_list, H_list, N_C, cumulativeDet_list = [], [], [], [], [], [], [], [], []
                                                                                            
        # Initial number of asymptomatic and symptomatic cases
        num_asy_init = int(p_asy*n_I_init)
        num_sy_init  = n_I_init-num_asy_init
        
        for day in range(num_days):
            p_e = p_e_vector[day]
            
            if (day == day_init):
                # at day_init we introduce given number of exposed and infected cases
                for m in range(M):
                    Asy_reg[m] = list(np.random.choice(L_s_reg[m].nodes(), num_asy_init, replace=False))
                    Sy_reg[m] = list(np.random.choice(list(set(L_s_reg[m].nodes()).difference(set(Asy_reg[m]))), num_sy_init, replace=False))
                    E_reg[m] = list(np.random.choice(list(set(L_s_reg[m].nodes()).difference(set(Asy_reg[m]+Sy_reg[m]))), n_E_init, replace=False))

            dH, dE, dR, dD, dAsy, dSy, cH, New_cases = 0, 0, 0, 0, 0, 0, 0, 0
            for m in range(M):
                if testing_policy[day] == 1:
                    policy  = 'symptomatic'
                elif testing_policy[day] == 2:
                    policy  = 'random'
                else:
                    policy  = 'no_testing'
                if contact_tracing[day] == 0:
                    tracing = False
                    p_ct = 0
                else:
                    tracing = True
                    if contact_tracing[day] == 1:
                        p_ct = probs_ct[0]
                    else:
                        p_ct = probs_ct[1]
                num_vac = vaccines[day]
                
                test_num = tests[day]

                if flag_hard_lock[day] or day == 0:
                    Graph = L_hard_lock_reg[m]

                elif flag_wp_sch[day] == '00':
                    Graph = R_l_reg[m]
                elif flag_wp_sch[day] == '01':
                    Graph = R_m_reg[m]
                elif flag_wp_sch[day] == '03':
                    Graph = R_m_reg[m]
                elif flag_wp_sch[day] == '10':
                    Graph = R_m_reg[m]
                elif flag_wp_sch[day] == '11':
                    Graph = R_m_reg[m]
                elif flag_wp_sch[day] == '13':
                    Graph = L_m_reg[m]
                elif flag_wp_sch[day] == '30':
                    Graph = R_s_reg[m]
                elif flag_wp_sch[day] == '31':
                    Graph = L_m_reg[m]
                elif flag_wp_sch[day] == '33':
                    Graph = L_s_reg[m]
                    
                # Local Values
                Det[m], Asy_reg[m], Sy_reg[m], H_reg[m], E_reg[m], R_reg[m], D_reg[m], Q_Asy_reg[m], Q_Sy_reg[m], Q_S_reg[m], \
                Q_E_reg[m], V_reg[m], dAsy_r, dSy_r, dE_r, dR_r, dH_r, dD_r, dQ_r, pos_num  = seird_iteration(Graph, Det[m], E_reg[m],
                                                                                                    R_reg[m], D_reg[m],
                                                                                                    Asy_reg[m],
                                                                                                    Sy_reg[m], H_reg[m],
                                                                                                    Q_Asy_reg[m],
                                                                                                    Q_Sy_reg[m],
                                                                                                    Q_S_reg[m],
                                                                                                    Q_E_reg[m],
                                                                                                    V_reg[m],
                                                                                                    kids_all_reg[m],
                                                                                                    p_e, p_i, p_r,
                                                                                                    p_h_d,
                                                                                                    p_h_r, p_asy,
                                                                                                    p_sy_h, v_eff, p_s,
                                                                                                    num_vac=int(num_vac/M),
                                                                                                    test_policy=policy,
                                                                                                    test_num=int(test_num/M),
                                                                                                    p_sy_t=p_sy_t,
                                                                                                    contact_tracing=tracing,
                                                                                                    p_ct=p_ct,
                                                                                                    return_count=True)

                # update global values
                dH  += dH_r
                dE  += dE_r
                dR  += dR_r
                dD  += dD_r
                dAsy+= dAsy_r
                dSy += dSy_r
                cH  += len(H_reg[m])
                New_cases += pos_num              
  
            # Global values
            dH_list.append(dH)
            dR_list.append(dR)
            dD_list.append(dD)
            dAsy_list.append(dAsy)
            dSy_list.append(dSy)
            H_list.append(cH)  # currently hospitalized
            N_C.append(New_cases)
            cumulativeDet_list.append(sum([len(set(Det[m]))for m in range(M)]))

            # new exposures from the interactions between the regions
            if flag_hard_lock[day]:
                mix_c = mix_perc[0]
            else:
                mix_c = mix_perc[1]
            W = np.ones((M, M)) * mix_c

            S_reg = [[] for m in range(M)]

            for m in range(M):
                S_reg[m] = list(set(L_s_reg[m].nodes()).difference(
                    Asy_reg[m] + Sy_reg[m] + H_reg[m] + E_reg[m] + R_reg[m] + D_reg[m] + Q_Asy_reg[m] + Q_Sy_reg[m] +
                    Q_S_reg[m] + Q_E_reg[m]))
            for j in range(M):
                n_new_contacts = int((sum([len(Asy_reg[i]) * W[i, j] for i in range(M) if i != j]) + sum(
                    [len(Sy_reg[i]) * W[i, j] for i in range(M) if i != j])) * len(S_reg[j]) / total_size)
                new_contacts    = set(np.random.choice(S_reg[j], replace=False, size=n_new_contacts))
                
                new_contacts_V  = np.array(list(new_contacts & set(V_reg[j])))
                new_contacts_NV = np.array(list(new_contacts.difference(set(V_reg[j]))))
                new_E_V   = list(new_contacts_V[np.where(np.random.rand(len(new_contacts_V))<p_e*(1-v_eff))[0]])
                new_E_NV  = list(new_contacts_NV[np.where(np.random.rand(len(new_contacts_NV))<p_e)[0]])
                E_reg[j] += new_E_V + new_E_NV
                E_reg[j]  = list(set(E_reg[j]))
                dE       += len(new_E_V) + len(new_E_NV)
            
            if flag_international[day]==0 and day > day_init:
                for m in range(M):
                    p = np.random.rand(1)
                    if p < p_international:
                        S_reg[m] = list(set(L_s_reg[m].nodes()).difference(
                        Asy_reg[m] + Sy_reg[m] + H_reg[m] + E_reg[m] + R_reg[m] + D_reg[m] + Q_Asy_reg[m] + Q_Sy_reg[m] +
                        Q_S_reg[m] + Q_E_reg[m]))
                        new_Exposed = list(np.random.choice(S_reg[m],size=max(1,int(0.000034*reg_sizes[m]))))
                        E_reg[m]   += new_Exposed
                        E_reg[m]    = list(set(E_reg[m]))
                        dE         += 1
            dE_list.append(dE)
     
        dH_mtx[repetition]   = dH_list
        dE_mtx[repetition]   = dE_list
        dR_mtx[repetition]   = dR_list
        dD_mtx[repetition]   = dD_list
        dAsy_mtx[repetition] = dAsy_list
        dSy_mtx[repetition]  = dSy_list
        cH_mtx[repetition]   = H_list
        NC_mtx[repetition]   = N_C

    return dH_mtx, dE_mtx, dR_mtx, dD_mtx, dAsy_mtx, dSy_mtx, cH_mtx, NC_mtx, cumulativeDet_list