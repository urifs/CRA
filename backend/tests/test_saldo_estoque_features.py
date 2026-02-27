"""
Test file for:
1. Quitar conta a RECEBER - saldo bancário deve AUMENTAR
2. Quitar conta a PAGAR - saldo bancário deve DIMINUIR
3. Stock items with machine_ids (vinculação de máquinas)
4. API de items retorna machine_ids e machine_names
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAuth:
    """Authentication helper"""
    
    @staticmethod
    def get_token():
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "password"
        })
        if response.status_code == 200:
            return response.json().get("token")
        return None


class TestQuitacaoSaldoBancario:
    """Test bank balance updates when settling accounts"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.token = TestAuth.get_token()
        assert self.token, "Failed to get auth token"
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.conta_bancaria_id = "395f583f-aa02-45c5-af64-c1c1c0b4206d"
    
    def test_01_get_initial_bank_balance(self):
        """Get initial bank account balance"""
        response = requests.get(f"{BASE_URL}/api/admin/contas-bancarias", headers=self.headers)
        assert response.status_code == 200, f"Failed to get bank accounts: {response.text}"
        
        contas = response.json()
        conta = next((c for c in contas if c.get("id") == self.conta_bancaria_id), None)
        
        if conta:
            print(f"Bank account found: {conta.get('nome')} - Saldo: R$ {conta.get('saldo_atual', 0):.2f}")
        else:
            print(f"Bank account {self.conta_bancaria_id} not found. Available accounts:")
            for c in contas[:5]:
                print(f"  - {c.get('id')}: {c.get('nome')} - R$ {c.get('saldo_atual', 0):.2f}")
    
    def test_02_quitar_conta_receber_aumenta_saldo(self):
        """Test: Quitar conta a RECEBER should INCREASE bank balance"""
        # Step 1: Get initial bank balance
        response = requests.get(f"{BASE_URL}/api/admin/contas-bancarias", headers=self.headers)
        assert response.status_code == 200
        contas = response.json()
        conta_bancaria = next((c for c in contas if c.get("id") == self.conta_bancaria_id), None)
        
        if not conta_bancaria:
            # Use first available account
            if contas:
                conta_bancaria = contas[0]
                self.conta_bancaria_id = conta_bancaria["id"]
            else:
                pytest.skip("No bank accounts available")
        
        saldo_inicial = conta_bancaria.get("saldo_atual", 0) or 0
        print(f"Initial balance: R$ {saldo_inicial:.2f}")
        
        # Step 2: Create a conta a receber (em_aberto)
        conta_receber_data = {
            "descricao": f"TEST_Recebimento_{uuid.uuid4().hex[:8]}",
            "valor": 500.00,
            "data_vencimento": "2025-12-31",
            "cliente_id": None,
            "cliente_nome": "TEST_Cliente",
            "status": "em_aberto",
            "categoria": "servicos"
        }
        response = requests.post(f"{BASE_URL}/api/admin/contas-receber", json=conta_receber_data, headers=self.headers)
        assert response.status_code == 200, f"Failed to create conta receber: {response.text}"
        conta_receber = response.json()
        conta_receber_id = conta_receber["id"]
        valor_conta = conta_receber.get("valor_final") or conta_receber.get("valor", 500.00)
        print(f"Created conta a receber: {conta_receber_id} - Valor: R$ {valor_conta:.2f}")
        
        # Step 3: Quitar the conta a receber with bank account
        quitar_data = {
            "data_recebimento": "2025-01-15",
            "conta_bancaria_id": self.conta_bancaria_id
        }
        response = requests.patch(f"{BASE_URL}/api/admin/contas-receber/{conta_receber_id}/quitar", json=quitar_data, headers=self.headers)
        assert response.status_code == 200, f"Failed to quitar conta receber: {response.text}"
        print(f"Conta a receber quitada successfully")
        
        # Step 4: Verify bank balance INCREASED
        response = requests.get(f"{BASE_URL}/api/admin/contas-bancarias", headers=self.headers)
        assert response.status_code == 200
        contas = response.json()
        conta_bancaria_updated = next((c for c in contas if c.get("id") == self.conta_bancaria_id), None)
        
        saldo_final = conta_bancaria_updated.get("saldo_atual", 0) or 0
        print(f"Final balance: R$ {saldo_final:.2f}")
        print(f"Expected increase: R$ {valor_conta:.2f}")
        print(f"Actual change: R$ {saldo_final - saldo_inicial:.2f}")
        
        # CRITICAL ASSERTION: Balance should INCREASE when receiving money
        assert saldo_final > saldo_inicial, f"Bank balance should INCREASE after quitar conta a receber. Initial: {saldo_inicial}, Final: {saldo_final}"
        assert abs((saldo_final - saldo_inicial) - valor_conta) < 0.01, f"Balance increase should match conta value. Expected: {valor_conta}, Got: {saldo_final - saldo_inicial}"
        
        print("✓ PASSED: Quitar conta a RECEBER correctly INCREASED bank balance")
    
    def test_03_quitar_conta_pagar_diminui_saldo(self):
        """Test: Quitar conta a PAGAR should DECREASE bank balance"""
        # Step 1: Get initial bank balance
        response = requests.get(f"{BASE_URL}/api/admin/contas-bancarias", headers=self.headers)
        assert response.status_code == 200
        contas = response.json()
        conta_bancaria = next((c for c in contas if c.get("id") == self.conta_bancaria_id), None)
        
        if not conta_bancaria:
            if contas:
                conta_bancaria = contas[0]
                self.conta_bancaria_id = conta_bancaria["id"]
            else:
                pytest.skip("No bank accounts available")
        
        saldo_inicial = conta_bancaria.get("saldo_atual", 0) or 0
        print(f"Initial balance: R$ {saldo_inicial:.2f}")
        
        # Step 2: Create a conta a pagar (em_aberto)
        conta_pagar_data = {
            "descricao": f"TEST_Pagamento_{uuid.uuid4().hex[:8]}",
            "valor": 300.00,
            "data_vencimento": "2025-12-31",
            "fornecedor_id": None,
            "fornecedor_nome": "TEST_Fornecedor",
            "status": "em_aberto",
            "categoria": "despesas"
        }
        response = requests.post(f"{BASE_URL}/api/admin/contas-pagar", json=conta_pagar_data, headers=self.headers)
        assert response.status_code == 200, f"Failed to create conta pagar: {response.text}"
        conta_pagar = response.json()
        conta_pagar_id = conta_pagar["id"]
        valor_conta = conta_pagar.get("valor_final") or conta_pagar.get("valor", 300.00)
        print(f"Created conta a pagar: {conta_pagar_id} - Valor: R$ {valor_conta:.2f}")
        
        # Step 3: Quitar the conta a pagar with bank account
        quitar_data = {
            "data_pagamento": "2025-01-15",
            "conta_bancaria_id": self.conta_bancaria_id
        }
        response = requests.patch(f"{BASE_URL}/api/admin/contas-pagar/{conta_pagar_id}/quitar", json=quitar_data, headers=self.headers)
        assert response.status_code == 200, f"Failed to quitar conta pagar: {response.text}"
        print(f"Conta a pagar quitada successfully")
        
        # Step 4: Verify bank balance DECREASED
        response = requests.get(f"{BASE_URL}/api/admin/contas-bancarias", headers=self.headers)
        assert response.status_code == 200
        contas = response.json()
        conta_bancaria_updated = next((c for c in contas if c.get("id") == self.conta_bancaria_id), None)
        
        saldo_final = conta_bancaria_updated.get("saldo_atual", 0) or 0
        print(f"Final balance: R$ {saldo_final:.2f}")
        print(f"Expected decrease: R$ {valor_conta:.2f}")
        print(f"Actual change: R$ {saldo_inicial - saldo_final:.2f}")
        
        # CRITICAL ASSERTION: Balance should DECREASE when paying
        assert saldo_final < saldo_inicial, f"Bank balance should DECREASE after quitar conta a pagar. Initial: {saldo_inicial}, Final: {saldo_final}"
        assert abs((saldo_inicial - saldo_final) - valor_conta) < 0.01, f"Balance decrease should match conta value. Expected: {valor_conta}, Got: {saldo_inicial - saldo_final}"
        
        print("✓ PASSED: Quitar conta a PAGAR correctly DECREASED bank balance")


class TestStockItemMachineVinculacao:
    """Test stock items with machine_ids linking"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.token = TestAuth.get_token()
        assert self.token, "Failed to get auth token"
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.created_items = []
        self.created_machines = []
    
    def teardown_method(self):
        """Cleanup test data"""
        for item_id in self.created_items:
            try:
                requests.delete(f"{BASE_URL}/api/stock/items/{item_id}", headers=self.headers)
            except:
                pass
        for machine_id in self.created_machines:
            try:
                requests.delete(f"{BASE_URL}/api/machines/{machine_id}", headers=self.headers)
            except:
                pass
    
    def test_01_get_machines_list(self):
        """Get list of available machines"""
        response = requests.get(f"{BASE_URL}/api/machines", headers=self.headers)
        assert response.status_code == 200, f"Failed to get machines: {response.text}"
        machines = response.json()
        print(f"Found {len(machines)} machines")
        if machines:
            for m in machines[:3]:
                print(f"  - {m.get('id')}: {m.get('name')} ({m.get('plate', 'N/A')})")
    
    def test_02_create_stock_item_with_machine_ids(self):
        """Test creating stock item with machine_ids"""
        # First get available machines
        response = requests.get(f"{BASE_URL}/api/machines", headers=self.headers)
        assert response.status_code == 200
        machines = response.json()
        
        machine_ids = []
        if machines:
            machine_ids = [m["id"] for m in machines[:2]]  # Link to first 2 machines
        
        # Create stock item with machine_ids
        item_data = {
            "name": f"TEST_Filtro_Oleo_{uuid.uuid4().hex[:8]}",
            "code": f"TEST-FO-{uuid.uuid4().hex[:4].upper()}",
            "category": "Filtros",
            "unit": "un",
            "quantity": 10,
            "min_quantity": 5,
            "unit_price": 45.90,
            "location": "Prateleira A1",
            "notes": "Item de teste com vinculação de máquinas",
            "machine_ids": machine_ids
        }
        
        response = requests.post(f"{BASE_URL}/api/stock/items", json=item_data, headers=self.headers)
        assert response.status_code == 200, f"Failed to create stock item: {response.text}"
        
        item = response.json()
        self.created_items.append(item["id"])
        
        print(f"Created stock item: {item['id']}")
        print(f"  Name: {item['name']}")
        print(f"  machine_ids: {item.get('machine_ids', [])}")
        print(f"  machine_names: {item.get('machine_names', [])}")
        
        # Verify machine_ids are saved
        assert "machine_ids" in item, "Response should contain machine_ids field"
        assert item.get("machine_ids") == machine_ids, f"machine_ids should match. Expected: {machine_ids}, Got: {item.get('machine_ids')}"
        
        # Verify machine_names are returned
        assert "machine_names" in item, "Response should contain machine_names field"
        if machine_ids:
            assert len(item.get("machine_names", [])) == len(machine_ids), "machine_names count should match machine_ids count"
        
        print("✓ PASSED: Stock item created with machine_ids and machine_names returned")
    
    def test_03_get_stock_items_returns_machine_fields(self):
        """Test that GET /stock/items returns machine_ids and machine_names"""
        response = requests.get(f"{BASE_URL}/api/stock/items", headers=self.headers)
        assert response.status_code == 200, f"Failed to get stock items: {response.text}"
        
        items = response.json()
        print(f"Found {len(items)} stock items")
        
        # Check that items have machine_ids and machine_names fields
        for item in items[:5]:
            print(f"  - {item['name']}: machine_ids={item.get('machine_ids', 'MISSING')}, machine_names={item.get('machine_names', 'MISSING')}")
            assert "machine_ids" in item, f"Item {item['name']} should have machine_ids field"
            assert "machine_names" in item, f"Item {item['name']} should have machine_names field"
        
        print("✓ PASSED: GET /stock/items returns machine_ids and machine_names")
    
    def test_04_update_stock_item_machine_ids(self):
        """Test updating stock item with different machine_ids"""
        # Get machines
        response = requests.get(f"{BASE_URL}/api/machines", headers=self.headers)
        machines = response.json() if response.status_code == 200 else []
        
        # Create item without machines
        item_data = {
            "name": f"TEST_Correia_{uuid.uuid4().hex[:8]}",
            "code": f"TEST-CR-{uuid.uuid4().hex[:4].upper()}",
            "category": "Correias",
            "unit": "un",
            "quantity": 5,
            "min_quantity": 2,
            "unit_price": 120.00,
            "machine_ids": []
        }
        
        response = requests.post(f"{BASE_URL}/api/stock/items", json=item_data, headers=self.headers)
        assert response.status_code == 200
        item = response.json()
        self.created_items.append(item["id"])
        
        print(f"Created item without machines: {item['id']}")
        assert item.get("machine_ids") == [], "Initial machine_ids should be empty"
        
        # Update with machine_ids
        if machines:
            new_machine_ids = [machines[0]["id"]]
            item_data["machine_ids"] = new_machine_ids
            
            response = requests.put(f"{BASE_URL}/api/stock/items/{item['id']}", json=item_data, headers=self.headers)
            assert response.status_code == 200, f"Failed to update item: {response.text}"
            
            updated_item = response.json()
            print(f"Updated item with machine_ids: {updated_item.get('machine_ids')}")
            print(f"Updated item machine_names: {updated_item.get('machine_names')}")
            
            assert updated_item.get("machine_ids") == new_machine_ids, "machine_ids should be updated"
            assert len(updated_item.get("machine_names", [])) > 0, "machine_names should be populated"
        
        print("✓ PASSED: Stock item machine_ids can be updated")
    
    def test_05_stock_item_multiple_machines(self):
        """Test stock item can be linked to multiple machines"""
        # Get machines
        response = requests.get(f"{BASE_URL}/api/machines", headers=self.headers)
        machines = response.json() if response.status_code == 200 else []
        
        if len(machines) < 2:
            pytest.skip("Need at least 2 machines for this test")
        
        # Create item with multiple machines
        machine_ids = [m["id"] for m in machines[:3]]  # Up to 3 machines
        
        item_data = {
            "name": f"TEST_Oleo_Motor_{uuid.uuid4().hex[:8]}",
            "code": f"TEST-OM-{uuid.uuid4().hex[:4].upper()}",
            "category": "Óleos",
            "unit": "L",
            "quantity": 50,
            "min_quantity": 20,
            "unit_price": 35.00,
            "machine_ids": machine_ids
        }
        
        response = requests.post(f"{BASE_URL}/api/stock/items", json=item_data, headers=self.headers)
        assert response.status_code == 200, f"Failed to create item: {response.text}"
        
        item = response.json()
        self.created_items.append(item["id"])
        
        print(f"Created item with {len(machine_ids)} machines")
        print(f"  machine_ids: {item.get('machine_ids')}")
        print(f"  machine_names: {item.get('machine_names')}")
        
        assert len(item.get("machine_ids", [])) == len(machine_ids), f"Should have {len(machine_ids)} machine_ids"
        assert len(item.get("machine_names", [])) == len(machine_ids), f"Should have {len(machine_ids)} machine_names"
        
        print("✓ PASSED: Stock item can be linked to multiple machines")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
