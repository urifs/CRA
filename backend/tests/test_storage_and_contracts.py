"""
Test Storage System and Aluguel Contract Features
- Storage: create folder, upload file, list items, rename, delete
- Aluguel: numero_contrato field and contract file upload/download
"""
import pytest
import requests
import os
import io

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAuth:
    """Get authentication token"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "password"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}


class TestStorageSystem(TestAuth):
    """Test Storage System CRUD operations"""
    
    def test_storage_list_root(self, headers):
        """Test listing storage items at root"""
        response = requests.get(f"{BASE_URL}/api/storage/list", 
                               params={"path": "/"}, 
                               headers=headers)
        assert response.status_code == 200, f"List failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"Root storage items: {len(data)}")
    
    def test_storage_create_folder(self, headers):
        """Test creating a new folder"""
        response = requests.post(f"{BASE_URL}/api/storage/folder",
                                json={"name": "TEST_folder_pytest", "parent_path": "/"},
                                headers=headers)
        assert response.status_code == 200, f"Create folder failed: {response.text}"
        data = response.json()
        assert "path" in data, "Response should contain path"
        assert "TEST_folder_pytest" in data["path"], "Path should contain folder name"
        print(f"Created folder: {data['path']}")
    
    def test_storage_create_folder_duplicate(self, headers):
        """Test creating duplicate folder should fail"""
        response = requests.post(f"{BASE_URL}/api/storage/folder",
                                json={"name": "TEST_folder_pytest", "parent_path": "/"},
                                headers=headers)
        assert response.status_code == 400, "Duplicate folder should return 400"
    
    def test_storage_upload_file(self, headers):
        """Test uploading a file"""
        # Create a test file
        file_content = b"Test file content for pytest storage test"
        files = {"file": ("TEST_file_pytest.txt", io.BytesIO(file_content), "text/plain")}
        data = {"path": "/"}
        
        response = requests.post(f"{BASE_URL}/api/storage/upload",
                                files=files,
                                data=data,
                                headers=headers)
        assert response.status_code == 200, f"Upload failed: {response.text}"
        result = response.json()
        assert "name" in result, "Response should contain name"
        assert "path" in result, "Response should contain path"
        print(f"Uploaded file: {result['name']} at {result['path']}")
    
    def test_storage_list_after_upload(self, headers):
        """Test listing items after upload"""
        response = requests.get(f"{BASE_URL}/api/storage/list",
                               params={"path": "/"},
                               headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        # Check if our test items exist
        names = [item["name"] for item in data]
        assert "TEST_folder_pytest" in names, "Test folder should exist"
        # File might have suffix if duplicate
        test_files = [n for n in names if n.startswith("TEST_file_pytest")]
        assert len(test_files) > 0, "Test file should exist"
        print(f"Found items: {names}")
    
    def test_storage_download_file(self, headers):
        """Test downloading a file"""
        # First get the file path
        response = requests.get(f"{BASE_URL}/api/storage/list",
                               params={"path": "/"},
                               headers=headers)
        data = response.json()
        test_files = [item for item in data if item["name"].startswith("TEST_file_pytest")]
        
        if test_files:
            file_path = test_files[0]["path"]
            response = requests.get(f"{BASE_URL}/api/storage/download",
                                   params={"path": file_path},
                                   headers=headers)
            assert response.status_code == 200, f"Download failed: {response.text}"
            assert len(response.content) > 0, "Downloaded content should not be empty"
            print(f"Downloaded file: {file_path}, size: {len(response.content)} bytes")
    
    def test_storage_rename_folder(self, headers):
        """Test renaming a folder"""
        response = requests.patch(f"{BASE_URL}/api/storage/rename",
                                 json={"path": "/TEST_folder_pytest", "new_name": "TEST_folder_renamed"},
                                 headers=headers)
        assert response.status_code == 200, f"Rename failed: {response.text}"
        data = response.json()
        assert "new_path" in data, "Response should contain new_path"
        print(f"Renamed folder to: {data['new_path']}")
    
    def test_storage_delete_folder(self, headers):
        """Test deleting a folder"""
        response = requests.delete(f"{BASE_URL}/api/storage/delete",
                                  params={"path": "/TEST_folder_renamed"},
                                  headers=headers)
        assert response.status_code == 200, f"Delete folder failed: {response.text}"
        print("Deleted test folder")
    
    def test_storage_delete_file(self, headers):
        """Test deleting uploaded test files"""
        # Get list of test files
        response = requests.get(f"{BASE_URL}/api/storage/list",
                               params={"path": "/"},
                               headers=headers)
        data = response.json()
        test_files = [item for item in data if item["name"].startswith("TEST_file_pytest")]
        
        for file in test_files:
            response = requests.delete(f"{BASE_URL}/api/storage/delete",
                                      params={"path": file["path"]},
                                      headers=headers)
            assert response.status_code == 200, f"Delete file failed: {response.text}"
            print(f"Deleted test file: {file['name']}")


class TestAluguelContractFeatures(TestAuth):
    """Test Aluguel contract number and file upload features"""
    
    @pytest.fixture(scope="class")
    def test_machine(self, headers):
        """Create a test machine for aluguel tests"""
        # First create a category
        cat_response = requests.post(f"{BASE_URL}/api/categories",
                                    json={"name": "TEST_Category_Aluguel", "description": "Test"},
                                    headers=headers)
        if cat_response.status_code == 200:
            category_id = cat_response.json()["id"]
        else:
            # Get existing category
            cats = requests.get(f"{BASE_URL}/api/categories", headers=headers).json()
            category_id = cats[0]["id"] if cats else None
        
        # Create machine
        machine_response = requests.post(f"{BASE_URL}/api/machines",
                                        json={
                                            "name": "TEST_Machine_Aluguel",
                                            "plate": "TEST-9999",
                                            "category_id": category_id
                                        },
                                        headers=headers)
        if machine_response.status_code == 200:
            return machine_response.json()
        else:
            # Get existing machine
            machines = requests.get(f"{BASE_URL}/api/machines", headers=headers).json()
            return machines[0] if machines else None
    
    def test_create_aluguel_with_contract_number(self, headers, test_machine):
        """Test creating aluguel with numero_contrato field"""
        if not test_machine:
            pytest.skip("No machine available for test")
        
        aluguel_data = {
            "maquina_id": test_machine["id"],
            "maquina_nome": test_machine["name"],
            "maquina_placa": test_machine.get("plate", ""),
            "cliente_nome": "TEST_Cliente_Pytest",
            "cliente_telefone": "(11) 99999-9999",
            "cliente_documento": "123.456.789-00",
            "numero_contrato": "CONT-TEST-2026-001",
            "tipo_periodo": "mensal",
            "data_entrega": "2026-01-25",
            "data_vencimento": "2026-02-25",
            "valor": 5000.00,
            "valor_caucao": 1000.00,
            "local_entrega": "Test Location",
            "observacoes": "Test observation",
            "gerar_conta_receber": False
        }
        
        response = requests.post(f"{BASE_URL}/api/admin/alugueis",
                                json=aluguel_data,
                                headers=headers)
        assert response.status_code == 200, f"Create aluguel failed: {response.text}"
        data = response.json()
        assert "id" in data, "Response should contain id"
        assert data.get("numero_contrato") == "CONT-TEST-2026-001", "Contract number should be saved"
        print(f"Created aluguel #{data.get('numero')} with contract: {data.get('numero_contrato')}")
        return data
    
    def test_upload_contract_file(self, headers, test_machine):
        """Test uploading contract file to aluguel"""
        # First create an aluguel
        aluguel_data = {
            "maquina_id": test_machine["id"],
            "maquina_nome": test_machine["name"],
            "maquina_placa": test_machine.get("plate", ""),
            "cliente_nome": "TEST_Cliente_Contract_Upload",
            "numero_contrato": "CONT-UPLOAD-TEST",
            "tipo_periodo": "diaria",
            "data_entrega": "2026-01-25",
            "data_vencimento": "2026-01-30",
            "valor": 1000.00,
            "gerar_conta_receber": False
        }
        
        response = requests.post(f"{BASE_URL}/api/admin/alugueis",
                                json=aluguel_data,
                                headers=headers)
        assert response.status_code == 200
        aluguel_id = response.json()["id"]
        
        # Upload contract file
        file_content = b"%PDF-1.4 Test PDF content for contract"
        files = {"file": ("contrato_test.pdf", io.BytesIO(file_content), "application/pdf")}
        
        response = requests.post(f"{BASE_URL}/api/admin/alugueis/{aluguel_id}/contrato",
                                files=files,
                                headers=headers)
        assert response.status_code == 200, f"Upload contract failed: {response.text}"
        data = response.json()
        assert "contrato_arquivo" in data, "Response should contain contrato_arquivo"
        print(f"Uploaded contract: {data.get('contrato_nome')}")
        return aluguel_id
    
    def test_download_contract_file(self, headers, test_machine):
        """Test downloading contract file from aluguel"""
        # Get alugueis list
        response = requests.get(f"{BASE_URL}/api/admin/alugueis", headers=headers)
        assert response.status_code == 200
        alugueis = response.json()
        
        # Find one with contract
        aluguel_with_contract = None
        for a in alugueis:
            if a.get("contrato_arquivo"):
                aluguel_with_contract = a
                break
        
        if not aluguel_with_contract:
            pytest.skip("No aluguel with contract found")
        
        # Download contract
        response = requests.get(f"{BASE_URL}/api/admin/alugueis/{aluguel_with_contract['id']}/contrato/download",
                               headers=headers)
        assert response.status_code == 200, f"Download contract failed: {response.text}"
        assert len(response.content) > 0, "Downloaded content should not be empty"
        print(f"Downloaded contract for aluguel #{aluguel_with_contract.get('numero')}")
    
    def test_list_alugueis_with_contract_info(self, headers):
        """Test that alugueis list includes contract information"""
        response = requests.get(f"{BASE_URL}/api/admin/alugueis", headers=headers)
        assert response.status_code == 200
        alugueis = response.json()
        
        # Check structure
        if alugueis:
            sample = alugueis[0]
            # These fields should exist in the response
            expected_fields = ["id", "numero", "maquina_nome", "cliente_nome", "valor", "status"]
            for field in expected_fields:
                assert field in sample, f"Field {field} should be in response"
            
            # Check for contract fields
            test_alugueis = [a for a in alugueis if "TEST" in a.get("cliente_nome", "")]
            for a in test_alugueis:
                if a.get("numero_contrato"):
                    print(f"Aluguel #{a['numero']}: Contract #{a['numero_contrato']}, File: {a.get('contrato_arquivo', 'None')}")
    
    def test_cleanup_test_alugueis(self, headers):
        """Cleanup test alugueis"""
        response = requests.get(f"{BASE_URL}/api/admin/alugueis", headers=headers)
        alugueis = response.json()
        
        for a in alugueis:
            if "TEST" in a.get("cliente_nome", ""):
                del_response = requests.delete(f"{BASE_URL}/api/admin/alugueis/{a['id']}", headers=headers)
                if del_response.status_code == 200:
                    print(f"Deleted test aluguel #{a['numero']}")


class TestStorageInvalidCases(TestAuth):
    """Test error handling for storage operations"""
    
    def test_storage_invalid_folder_name(self, headers):
        """Test creating folder with invalid name"""
        response = requests.post(f"{BASE_URL}/api/storage/folder",
                                json={"name": "invalid/name", "parent_path": "/"},
                                headers=headers)
        assert response.status_code == 400, "Invalid folder name should return 400"
    
    def test_storage_download_nonexistent(self, headers):
        """Test downloading non-existent file"""
        response = requests.get(f"{BASE_URL}/api/storage/download",
                               params={"path": "/nonexistent_file_12345.txt"},
                               headers=headers)
        assert response.status_code == 404, "Non-existent file should return 404"
    
    def test_storage_delete_nonexistent(self, headers):
        """Test deleting non-existent item"""
        response = requests.delete(f"{BASE_URL}/api/storage/delete",
                                  params={"path": "/nonexistent_item_12345"},
                                  headers=headers)
        assert response.status_code == 404, "Non-existent item should return 404"
    
    def test_storage_rename_nonexistent(self, headers):
        """Test renaming non-existent item"""
        response = requests.patch(f"{BASE_URL}/api/storage/rename",
                                 json={"path": "/nonexistent_12345", "new_name": "new_name"},
                                 headers=headers)
        assert response.status_code == 404, "Non-existent item should return 404"


class TestStorageWithoutAuth:
    """Test storage endpoints require authentication"""
    
    def test_storage_list_no_auth(self):
        """Test listing without auth should fail"""
        response = requests.get(f"{BASE_URL}/api/storage/list", params={"path": "/"})
        assert response.status_code in [401, 403], "Should require authentication"
    
    def test_storage_upload_no_auth(self):
        """Test upload without auth should fail"""
        files = {"file": ("test.txt", io.BytesIO(b"test"), "text/plain")}
        response = requests.post(f"{BASE_URL}/api/storage/upload", files=files, data={"path": "/"})
        assert response.status_code in [401, 403], "Should require authentication"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
